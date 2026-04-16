from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.models import User, GameEvent, StealRecord, Withdrawal, WithdrawStatus, EventType
from app.services.game_service import (
    get_or_create_user, feed_chickens, collect_eggs,
    check_chicken_alive, steal_eggs, buy_item,
    get_feeder_level, should_trader_appear, days_until_trader
)

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class InitRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    language: str = "ru"
    referral_code: Optional[str] = None


class BuyRequest(BaseModel):
    item: str
    quantity: int = 1


class WithdrawRequest(BaseModel):
    amount: float


class StealRequest(BaseModel):
    victim_user_id: int


class NicknameRequest(BaseModel):
    nickname: str


class WalletRequest(BaseModel):
    wallet_address: str


# ─── Auth & State ─────────────────────────────────────────────────────────────

def serialize_user(user: User) -> dict:
    feeder = get_feeder_level(user)
    trader_active = should_trader_appear(user)
    days_until = days_until_trader(user)
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "nickname": user.nickname,
        "username": user.username,
        "language": user.language,
        "game_day": user.game_day,
        "chickens": user.chickens,
        "super_chickens": user.super_chickens,
        "feed_bags": user.feed_bags,
        "eggs_collected": user.eggs_collected,
        "balance_usd": round(user.balance_usd, 4),
        "balance_ton": round(user.balance_ton, 6),
        "has_glove": user.has_glove,
        "has_dog": user.has_dog,
        "has_auto_feeder": user.has_auto_feeder,
        "feeder_level": feeder,
        "last_fed_at": user.last_fed_at.isoformat() if user.last_fed_at else None,
        "ton_wallet": user.ton_wallet,
        "referral_code": user.referral_code,
        "tutorial_completed": user.tutorial_completed,
        "tutorial_market_done": user.tutorial_market_done,
        "trader_active": trader_active,
        "days_until_trader": days_until,
    }


@router.post("/auth/init")
async def init_player(req: InitRequest, db: AsyncSession = Depends(get_db)):
    """Initialize or get player. Called on app open."""
    user, is_new = await get_or_create_user(
        db,
        telegram_id=req.telegram_id,
        username=req.username,
        language=req.language,
        referral_code=req.referral_code,
    )

    # Check chicken alive status
    alive_info = await check_chicken_alive(db, user)

    return {
        "user": serialize_user(user),
        "is_new": is_new,
        "chicken_alive": alive_info,
    }


@router.get("/me")
async def get_me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    alive_info = await check_chicken_alive(db, user)
    return {"user": serialize_user(user), "chicken_alive": alive_info}


# ─── Game Actions ─────────────────────────────────────────────────────────────

@router.post("/game/feed")
async def feed(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    return await feed_chickens(db, user)


@router.post("/game/collect")
async def collect(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    return await collect_eggs(db, user)


@router.post("/game/steal")
async def steal(
    req: StealRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    thief = result.scalar_one_or_none()
    if not thief:
        raise HTTPException(404, "User not found")

    return await steal_eggs(db, thief, req.victim_user_id)


@router.post("/game/tutorial/complete")
async def complete_tutorial(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.tutorial_completed = True
    return {"ok": True}


@router.post("/game/tutorial/market-complete")
async def complete_market_tutorial(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.tutorial_market_done = True
    return {"ok": True}


# ─── Shop ──────────────────────────────────────────────────────────────────────

@router.post("/shop/buy")
async def shop_buy(
    req: BuyRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    return await buy_item(db, user, req.item, req.quantity)


@router.get("/shop/prices")
async def get_prices():
    """Return all current shop prices (pulled from game settings)."""
    from app.core.config import settings as s
    return {
        "chicken": {"usd": s.CHICKEN_COST_USD, "label": "chicken"},
        "feed": {"usd": s.FEED_COST_USD, "label": "feed"},
        "glove": {"usd": s.GLOVE_COST_USD, "label": "glove"},
        "dog": {"usd": s.DOG_COST_USD, "label": "dog"},
        "super_chicken": {"usd": s.SUPER_CHICKEN_COST_USD, "label": "super_chicken"},
        "auto_feeder": {"usd": None, "percent": s.AUTO_FEEDER_COST_PERCENT, "label": "auto_feeder"},
    }


# ─── Leaderboard ──────────────────────────────────────────────────────────────

@router.get("/leaderboard")
async def leaderboard(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.is_blocked == False)
        .order_by(desc(User.balance_usd))
        .limit(limit)
    )
    users = result.scalars().all()

    return {
        "leaders": [
            {
                "rank": i + 1,
                "id": u.id,
                "nickname": u.nickname,
                "balance_usd": round(u.balance_usd, 2),
                "chickens": u.chickens,
                "game_day": u.game_day,
                "has_dog": u.has_dog,
            }
            for i, u in enumerate(users)
        ]
    }


@router.get("/leaderboard/player/{player_id}")
async def get_player_farm(
    player_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """View another player's farm."""
    result = await db.execute(select(User).where(User.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, "Player not found")

    # Check if eggs already stolen today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    steal_check = await db.execute(
        select(StealRecord).where(
            and_(
                StealRecord.victim_id == player_id,
                StealRecord.stolen_at >= today_start,
            )
        )
    )
    already_stolen = steal_check.scalar_one_or_none() is not None

    return {
        "id": player.id,
        "nickname": player.nickname,
        "chickens": player.chickens,
        "super_chickens": player.super_chickens,
        "game_day": player.game_day,
        "has_dog": player.has_dog,
        "eggs_today": round((player.chickens + player.super_chickens * 2) * 0.20, 2),
        "already_stolen_today": already_stolen,
    }


# ─── Settings ─────────────────────────────────────────────────────────────────

@router.patch("/settings/nickname")
async def update_nickname(
    req: NicknameRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if len(req.nickname) < 2 or len(req.nickname) > 32:
        raise HTTPException(400, "Nickname must be 2-32 chars")

    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    old_nick = user.nickname
    user.nickname = req.nickname.strip()

    from app.models.models import GameEvent
    event = GameEvent(
        user_id=user.id,
        event_type=EventType.nickname_changed,
        data={"old": old_nick, "new": user.nickname},
    )
    db.add(event)
    return {"ok": True, "nickname": user.nickname}


@router.patch("/settings/wallet")
async def update_wallet(
    req: WalletRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    old_wallet = user.ton_wallet
    user.ton_wallet = req.wallet_address.strip()

    from app.models.models import GameEvent
    event = GameEvent(
        user_id=user.id,
        event_type=EventType.ton_wallet_linked,
        data={"old_wallet": old_wallet, "new_wallet": user.ton_wallet},
    )
    db.add(event)
    return {"ok": True, "wallet": user.ton_wallet}


@router.patch("/settings/language")
async def update_language(
    language: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    allowed = {"ru", "en", "zh", "hi", "es", "fr", "ar", "bn", "pt", "ur"}
    if language not in allowed:
        raise HTTPException(400, "Invalid language")

    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.language = language
    return {"ok": True}


@router.get("/settings/referrals")
async def get_referrals(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    ref_result = await db.execute(
        select(func.count(User.id)).where(User.referred_by_id == user.id)
    )
    ref_count = ref_result.scalar() or 0

    return {
        "referral_code": user.referral_code,
        "referral_link": f"https://t.me/YourBot?start=ref_{user.referral_code}",
        "referred_count": ref_count,
    }


# ─── Withdrawals ──────────────────────────────────────────────────────────────

@router.post("/withdraw/request")
async def request_withdrawal(
    req: WithdrawRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    if not user.ton_wallet:
        return {"success": False, "reason": "no_wallet"}

    if user.balance_usd < req.amount or req.amount <= 0:
        return {"success": False, "reason": "insufficient_balance"}

    withdrawal = Withdrawal(
        user_id=user.id,
        amount_usd=req.amount,
        ton_wallet=user.ton_wallet,
        status=WithdrawStatus.pending,
    )
    db.add(withdrawal)
    user.balance_usd -= req.amount

    from app.models.models import GameEvent
    event = GameEvent(
        user_id=user.id,
        event_type=EventType.withdraw_requested,
        data={"amount": req.amount, "wallet": user.ton_wallet},
    )
    db.add(event)

    return {"success": True, "message": "Withdrawal request submitted"}


@router.get("/withdraw/history")
async def withdrawal_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    wd_result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.user_id == user.id)
        .order_by(desc(Withdrawal.created_at))
        .limit(20)
    )
    withdrawals = wd_result.scalars().all()

    return {
        "history": [
            {
                "id": w.id,
                "amount": w.amount_usd,
                "status": w.status.value,
                "wallet": w.ton_wallet,
                "date": w.created_at.isoformat(),
            }
            for w in withdrawals
        ]
    }
