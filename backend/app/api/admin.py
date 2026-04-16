from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, update
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import get_admin_user
from app.models.models import (
    User, GameEvent, Withdrawal, WithdrawStatus,
    Transaction, AdminLog, GameSettings, Translation, EventType
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AdminGiveItem(BaseModel):
    item: str
    quantity: int = 1
    reason: str


class AdminUpdateUser(BaseModel):
    nickname: Optional[str] = None
    is_blocked: Optional[bool] = None
    balance_usd: Optional[float] = None
    feed_bags: Optional[int] = None
    chickens: Optional[int] = None


class WithdrawAction(BaseModel):
    action: str  # approve / reject / complete
    comment: Optional[str] = None


class GameSettingUpdate(BaseModel):
    key: str
    value: str


class TranslationUpdate(BaseModel):
    phrase_key: str
    lang: str
    text: str


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def admin_dashboard(
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    new_today = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= now.replace(hour=0, minute=0, second=0))
    )).scalar()
    active_24h = (await db.execute(
        select(func.count(User.id)).where(User.last_active_at >= day_ago)
    )).scalar()
    new_week = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar()

    total_balance = (await db.execute(select(func.sum(User.balance_usd)))).scalar() or 0
    total_ton = (await db.execute(select(func.sum(User.balance_ton)))).scalar() or 0

    avg_chickens = (await db.execute(select(func.avg(User.chickens)))).scalar() or 0
    avg_game_day = (await db.execute(select(func.avg(User.game_day)))).scalar() or 0

    has_glove_count = (await db.execute(
        select(func.count(User.id)).where(User.has_glove == True)
    )).scalar()
    has_dog_count = (await db.execute(
        select(func.count(User.id)).where(User.has_dog == True)
    )).scalar()
    has_auto_count = (await db.execute(
        select(func.count(User.id)).where(User.has_auto_feeder == True)
    )).scalar()

    # Top 10 players
    top_result = await db.execute(
        select(User).order_by(desc(User.balance_usd)).limit(10)
    )
    top_players = top_result.scalars().all()

    # Recent events
    events_result = await db.execute(
        select(GameEvent).order_by(desc(GameEvent.created_at)).limit(20)
    )
    recent_events = events_result.scalars().all()

    # Pending withdrawals count
    pending_wd = (await db.execute(
        select(func.count(Withdrawal.id)).where(Withdrawal.status == WithdrawStatus.pending)
    )).scalar()

    return {
        "stats": {
            "total_users": total_users,
            "new_today": new_today,
            "new_week": new_week,
            "active_24h": active_24h,
            "total_balance_usd": round(total_balance, 2),
            "total_ton_deposited": round(total_ton, 4),
            "avg_chickens": round(avg_chickens, 2),
            "avg_game_day": round(avg_game_day, 1),
            "has_glove_count": has_glove_count,
            "has_dog_count": has_dog_count,
            "has_auto_feeder_count": has_auto_count,
            "pending_withdrawals": pending_wd,
        },
        "top_players": [
            {"rank": i+1, "id": u.id, "nickname": u.nickname, "balance": round(u.balance_usd, 2)}
            for i, u in enumerate(top_players)
        ],
        "recent_events": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "type": e.event_type.value,
                "data": e.data,
                "at": e.created_at.isoformat(),
            }
            for e in recent_events
        ],
    }


# ─── Players ──────────────────────────────────────────────────────────────────

@router.get("/players")
async def list_players(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(desc(User.created_at))
    if search:
        query = query.where(
            (User.nickname.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%")) |
            (User.telegram_id.cast(str).like(f"%{search}%"))
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * limit).limit(limit))
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "players": [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "nickname": u.nickname,
                "username": u.username,
                "game_day": u.game_day,
                "chickens": u.chickens,
                "balance_usd": round(u.balance_usd, 2),
                "feed_bags": u.feed_bags,
                "has_glove": u.has_glove,
                "has_dog": u.has_dog,
                "is_blocked": u.is_blocked,
                "created_at": u.created_at.isoformat(),
                "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
            }
            for u in users
        ],
    }


@router.get("/players/{player_id}")
async def get_player_detail(
    player_id: int,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == player_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Player not found")

    events_result = await db.execute(
        select(GameEvent)
        .where(GameEvent.user_id == player_id)
        .order_by(desc(GameEvent.created_at))
        .limit(50)
    )
    events = events_result.scalars().all()

    return {
        "player": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "nickname": user.nickname,
            "username": user.username,
            "email": user.email,
            "language": user.language,
            "role": user.role.value,
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
            "ton_wallet": user.ton_wallet,
            "is_blocked": user.is_blocked,
            "created_at": user.created_at.isoformat(),
            "last_active_at": user.last_active_at.isoformat() if user.last_active_at else None,
        },
        "events": [
            {
                "type": e.event_type.value,
                "data": e.data,
                "at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }


@router.patch("/players/{player_id}")
async def update_player(
    player_id: int,
    req: AdminUpdateUser,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == player_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    changes = {}
    if req.nickname is not None:
        user.nickname = req.nickname
        changes["nickname"] = req.nickname
    if req.is_blocked is not None:
        user.is_blocked = req.is_blocked
        changes["is_blocked"] = req.is_blocked
    if req.balance_usd is not None:
        changes["balance_usd_delta"] = req.balance_usd - user.balance_usd
        user.balance_usd = req.balance_usd
    if req.feed_bags is not None:
        user.feed_bags = req.feed_bags
        changes["feed_bags"] = req.feed_bags
    if req.chickens is not None:
        user.chickens = req.chickens
        changes["chickens"] = req.chickens

    log = AdminLog(
        admin_id=admin_id,
        action="update_player",
        target_user_id=player_id,
        details=changes,
    )
    db.add(log)
    return {"ok": True, "changes": changes}


@router.post("/players/{player_id}/give")
async def give_item(
    player_id: int,
    req: AdminGiveItem,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == player_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    if req.item == "feed":
        user.feed_bags += req.quantity
    elif req.item == "chicken":
        user.chickens += req.quantity
    elif req.item == "glove":
        user.has_glove = True
    elif req.item == "dog":
        user.has_dog = True
    elif req.item == "auto_feeder":
        user.has_auto_feeder = True
    elif req.item == "balance_usd":
        user.balance_usd += req.quantity
    else:
        raise HTTPException(400, "Unknown item")

    log = AdminLog(
        admin_id=admin_id,
        action="give_item",
        target_user_id=player_id,
        details={"item": req.item, "quantity": req.quantity, "reason": req.reason},
    )
    db.add(log)

    event = GameEvent(
        user_id=player_id,
        event_type=EventType.admin_gave_item,
        data={"item": req.item, "quantity": req.quantity, "admin_id": admin_id},
    )
    db.add(event)

    return {"ok": True}


# ─── Withdrawals ──────────────────────────────────────────────────────────────

@router.get("/withdrawals")
async def list_withdrawals(
    status: Optional[str] = None,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Withdrawal).order_by(desc(Withdrawal.created_at))
    if status:
        query = query.where(Withdrawal.status == status)

    result = await db.execute(query.limit(200))
    withdrawals = result.scalars().all()

    return {
        "withdrawals": [
            {
                "id": w.id,
                "user_id": w.user_id,
                "amount_usd": w.amount_usd,
                "ton_wallet": w.ton_wallet,
                "status": w.status.value,
                "comment": w.admin_comment,
                "created_at": w.created_at.isoformat(),
            }
            for w in withdrawals
        ]
    }


@router.patch("/withdrawals/{withdrawal_id}")
async def update_withdrawal(
    withdrawal_id: int,
    req: WithdrawAction,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    wd = result.scalar_one_or_none()
    if not wd:
        raise HTTPException(404)

    if req.action == "approve":
        wd.status = WithdrawStatus.processing
    elif req.action == "reject":
        wd.status = WithdrawStatus.rejected
        # Refund to user
        user_result = await db.execute(select(User).where(User.id == wd.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.balance_usd += wd.amount_usd
    elif req.action == "complete":
        wd.status = WithdrawStatus.completed
    else:
        raise HTTPException(400, "Invalid action")

    if req.comment:
        wd.admin_comment = req.comment

    log = AdminLog(
        admin_id=admin_id,
        action=f"withdrawal_{req.action}",
        target_user_id=wd.user_id,
        details={"withdrawal_id": withdrawal_id, "action": req.action},
    )
    db.add(log)
    return {"ok": True, "status": wd.status.value}


# ─── Game Settings ────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_game_settings(
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.config import settings as s
    return {
        "egg_value_usd": s.EGG_VALUE_USD,
        "feed_cost_usd": s.FEED_COST_USD,
        "chicken_cost_usd": s.CHICKEN_COST_USD,
        "glove_cost_usd": s.GLOVE_COST_USD,
        "super_chicken_cost_usd": s.SUPER_CHICKEN_COST_USD,
        "dog_cost_usd": s.DOG_COST_USD,
        "steal_percent": s.STEAL_PERCENT,
        "trader_interval_days": s.TRADER_INTERVAL_DAYS,
        "trader_discount_percent": s.TRADER_DISCOUNT_PERCENT,
        "feed_death_hours": s.FEED_DEATH_HOURS,
        "death_warning_hours": s.DEATH_WARNING_HOURS,
        "referral_feed_bonus": s.REFERRAL_FEED_BONUS,
        "max_chickens_visual": s.MAX_CHICKENS_VISUAL,
    }


# ─── Translations ─────────────────────────────────────────────────────────────

@router.get("/translations")
async def get_translations(
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Translation))
    translations = result.scalars().all()
    return {
        "translations": [
            {
                "key": t.phrase_key,
                "ru": t.ru, "en": t.en, "zh": t.zh,
                "hi": t.hi, "es": t.es, "fr": t.fr,
                "ar": t.ar, "bn": t.bn, "pt": t.pt, "ur": t.ur,
            }
            for t in translations
        ]
    }


@router.patch("/translations")
async def update_translation(
    req: TranslationUpdate,
    admin_id: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Translation
    result = await db.execute(
        select(Translation).where(Translation.phrase_key == req.phrase_key)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Phrase key not found")

    allowed_langs = {"ru", "en", "zh", "hi", "es", "fr", "ar", "bn", "pt", "ur"}
    if req.lang not in allowed_langs:
        raise HTTPException(400, "Invalid language")

    setattr(t, req.lang, req.text)
    return {"ok": True}
