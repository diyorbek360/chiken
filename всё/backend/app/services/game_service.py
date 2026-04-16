from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from typing import Optional, Dict, Any
import random
import string

from app.models.models import User, GameEvent, StealRecord, Transaction, EventType
from app.core.config import settings


def utcnow():
    return datetime.now(timezone.utc)


def make_referral_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


async def get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: str = None,
    language: str = "ru",
    referral_code: str = None,
) -> tuple[User, bool]:
    """Get existing user or create new one. Returns (user, is_new)."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        user.last_active_at = utcnow()
        if username:
            user.username = username
        return user, False

    # Find referrer
    referrer = None
    if referral_code:
        ref_result = await db.execute(
            select(User).where(User.referral_code == referral_code)
        )
        referrer = ref_result.scalar_one_or_none()

    user = User(
        telegram_id=telegram_id,
        username=username,
        nickname=username or f"Player_{telegram_id % 10000}",
        language=language,
        referral_code=make_referral_code(),
        referred_by_id=referrer.id if referrer else None,
        feed_bags=0,
        last_active_at=utcnow(),
    )
    db.add(user)
    await db.flush()

    await log_event(db, user.id, EventType.registered, {
        "telegram_id": telegram_id,
        "referrer_id": referrer.id if referrer else None,
    })

    return user, True


async def log_event(
    db: AsyncSession,
    user_id: int,
    event_type: EventType,
    data: Dict[str, Any] = None,
):
    event = GameEvent(user_id=user_id, event_type=event_type, data=data)
    db.add(event)


async def feed_chickens(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Feed chickens - core daily action."""
    if user.feed_bags < 1:
        return {"success": False, "error": "no_feed", "message": "Not enough feed bags"}

    now = utcnow()
    is_first_feed = user.last_fed_at is None

    # Use 1 feed bag per chicken (capped at chicken count)
    bags_needed = user.chickens + user.super_chickens
    if user.feed_bags < bags_needed:
        bags_needed = user.feed_bags  # feed as many as we can

    user.feed_bags -= bags_needed
    user.feeder_level = 1.0  # reset to full
    user.last_fed_at = now

    event_type = EventType.first_feed if is_first_feed else EventType.fed_chickens
    await log_event(db, user.id, event_type, {
        "bags_used": bags_needed,
        "chickens": user.chickens,
        "remaining_bags": user.feed_bags,
    })

    # First feed triggers referral bonus to referrer
    if is_first_feed and user.referred_by_id:
        ref_result = await db.execute(select(User).where(User.id == user.referred_by_id))
        referrer = ref_result.scalar_one_or_none()
        if referrer:
            bonus = settings.REFERRAL_FEED_BONUS  # 3 bags early bonus
            referrer.feed_bags += bonus
            await log_event(db, referrer.id, EventType.referral_activated, {
                "new_player_id": user.id,
                "feed_bonus": bonus,
            })

    return {
        "success": True,
        "bags_used": bags_needed,
        "remaining_bags": user.feed_bags,
        "feeder_level": user.feeder_level,
        "is_first_feed": is_first_feed,
    }


async def collect_eggs(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Collect accumulated eggs from the tray."""
    now = utcnow()

    # Calculate eggs based on time since last collection (or last feed)
    last_ref = user.last_fed_at or user.created_at
    if not last_ref:
        return {"success": False, "eggs": 0, "earned": 0}

    hours_passed = (now - last_ref.replace(tzinfo=timezone.utc)).total_seconds() / 3600
    hours_passed = min(hours_passed, 24)  # cap at 24h

    total_chickens = user.chickens + (user.super_chickens * 2)  # super chicken = 2x
    daily_eggs_per_chicken = 1  # 1 egg = $0.20 per chicken per day
    eggs_available = int((hours_passed / 24) * total_chickens * daily_eggs_per_chicken)

    if eggs_available <= 0:
        return {"success": True, "eggs": 0, "earned": 0}

    earned_usd = eggs_available * settings.EGG_VALUE_USD
    user.eggs_collected += eggs_available
    user.balance_usd += earned_usd

    await log_event(db, user.id, EventType.eggs_collected, {
        "eggs": eggs_available,
        "earned_usd": earned_usd,
        "chickens": total_chickens,
    })

    t = Transaction(
        user_id=user.id,
        type="egg_income",
        amount=earned_usd,
        currency="USD",
        description=f"Collected {eggs_available} eggs",
    )
    db.add(t)

    return {"success": True, "eggs": eggs_available, "earned": earned_usd}


async def check_chicken_alive(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Check if chickens are still alive. Kill them if starved."""
    if user.last_fed_at is None:
        return {"alive": True, "hours_remaining": 24}

    now = utcnow()
    fed_at = user.last_fed_at.replace(tzinfo=timezone.utc)
    hours_since_feed = (now - fed_at).total_seconds() / 3600
    hours_remaining = settings.FEED_DEATH_HOURS - hours_since_feed

    if hours_remaining <= 0:
        # Chickens die
        user.chickens = 1
        user.super_chickens = 0
        user.has_glove = False
        user.has_dog = False
        user.has_auto_feeder = False
        user.feeder_level = 0.0
        user.last_fed_at = None
        user.game_day = 0
        # feed_bags and balance_usd are preserved!

        await log_event(db, user.id, EventType.chicken_died, {
            "hours_starved": hours_since_feed,
        })

        return {"alive": False, "hours_remaining": 0, "died": True}

    return {
        "alive": True,
        "hours_remaining": max(0, hours_remaining),
        "warning": hours_remaining <= settings.DEATH_WARNING_HOURS,
    }


async def steal_eggs(
    db: AsyncSession, thief: User, victim_id: int
) -> Dict[str, Any]:
    """Attempt to steal eggs from another player."""
    if not thief.has_glove:
        return {"success": False, "reason": "no_glove"}

    if thief.id == victim_id:
        return {"success": False, "reason": "cannot_steal_self"}

    # Get victim
    result = await db.execute(select(User).where(User.id == victim_id))
    victim = result.scalar_one_or_none()
    if not victim:
        return {"success": False, "reason": "victim_not_found"}

    # Check dog protection
    if victim.has_dog:
        await log_event(db, thief.id, EventType.steal_blocked_dog, {"victim_id": victim_id})
        return {"success": False, "reason": "dog_protection"}

    # Check if already stolen today
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    steal_check = await db.execute(
        select(StealRecord).where(
            and_(
                StealRecord.victim_id == victim_id,
                StealRecord.stolen_at >= today_start,
            )
        )
    )
    existing_steal = steal_check.scalar_one_or_none()
    if existing_steal:
        return {"success": False, "reason": "already_stolen_today"}

    # Calculate 10% of daily yield
    total_chickens = victim.chickens + (victim.super_chickens * 2)
    daily_yield = total_chickens * settings.EGG_VALUE_USD
    stolen_amount = daily_yield * (settings.STEAL_PERCENT / 100)

    if stolen_amount <= 0:
        return {"success": False, "reason": "nothing_to_steal"}

    # Execute steal
    victim.balance_usd = max(0, victim.balance_usd - stolen_amount)
    thief.balance_usd += stolen_amount

    record = StealRecord(
        thief_id=thief.id,
        victim_id=victim_id,
        eggs_amount=stolen_amount,
    )
    db.add(record)

    await log_event(db, thief.id, EventType.eggs_stolen, {
        "victim_id": victim_id,
        "amount_usd": stolen_amount,
    })
    await log_event(db, victim_id, EventType.steal_attempt, {
        "thief_id": thief.id,
        "amount_usd": stolen_amount,
    })

    return {"success": True, "amount_usd": stolen_amount}


async def buy_item(
    db: AsyncSession, user: User, item: str, quantity: int = 1
) -> Dict[str, Any]:
    """Purchase item from shop."""
    prices = {
        "chicken": settings.CHICKEN_COST_USD,
        "feed": settings.FEED_COST_USD,
        "glove": settings.GLOVE_COST_USD,
        "dog": settings.DOG_COST_USD,
        "super_chicken": settings.SUPER_CHICKEN_COST_USD,
        "auto_feeder": settings.AUTO_FEEDER_COST_PERCENT / 100 * max(user.balance_usd, 1),
    }

    if item not in prices:
        return {"success": False, "error": "unknown_item"}

    # One-time items
    one_time = {"glove", "dog", "auto_feeder"}
    if item in one_time and quantity != 1:
        quantity = 1
    if item == "glove" and user.has_glove:
        return {"success": False, "error": "already_owned"}
    if item == "dog" and user.has_dog:
        return {"success": False, "error": "already_owned"}
    if item == "auto_feeder" and user.has_auto_feeder:
        return {"success": False, "error": "already_owned"}

    total_cost = prices[item] * quantity
    if user.balance_usd < total_cost:
        return {"success": False, "error": "insufficient_balance", "needed": total_cost}

    user.balance_usd -= total_cost

    if item == "chicken":
        user.chickens += quantity
    elif item == "feed":
        user.feed_bags += quantity
    elif item == "glove":
        user.has_glove = True
    elif item == "dog":
        user.has_dog = True
    elif item == "auto_feeder":
        user.has_auto_feeder = True
    elif item == "super_chicken":
        user.super_chickens += quantity

    t = Transaction(
        user_id=user.id,
        type="purchase",
        amount=-total_cost,
        currency="USD",
        description=f"Bought {quantity}x {item}",
    )
    db.add(t)

    await log_event(db, user.id, EventType.bought_item, {
        "item": item,
        "quantity": quantity,
        "cost": total_cost,
    })

    return {"success": True, "item": item, "quantity": quantity, "cost": total_cost}


def get_feeder_level(user: User) -> float:
    """Return current feeder level 0.0-1.0 based on time elapsed."""
    if user.last_fed_at is None:
        return 0.0
    now = utcnow()
    fed_at = user.last_fed_at.replace(tzinfo=timezone.utc)
    elapsed = (now - fed_at).total_seconds() / 3600
    remaining_ratio = max(0, 1 - (elapsed / settings.FEED_DEATH_HOURS))
    return round(remaining_ratio, 3)


def should_trader_appear(user: User) -> bool:
    """Check if trader should be on farm (days 11-12 of each 10-day cycle)."""
    if user.game_day <= 0:
        return False
    cycle_day = user.game_day % settings.TRADER_INTERVAL_DAYS
    return cycle_day in (1, 2)  # day 11 and 12 of each cycle (mod 10 = 1, 2)


def days_until_trader(user: User) -> int:
    """Days until next trader visit."""
    if should_trader_appear(user):
        return 0
    cycle_day = user.game_day % settings.TRADER_INTERVAL_DAYS
    return settings.TRADER_INTERVAL_DAYS - cycle_day
