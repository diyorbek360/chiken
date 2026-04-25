"""
bot_service.py — Telegram Bot for notifications and payments.
"""
import asyncio
import logging
from typing import List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


async def send_message(chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message to a user."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send TG message to {chat_id}: {e}")
        return False


async def send_death_warning(telegram_id: int, hours_left: float, lang: str = "ru") -> bool:
    """Notify player that chicken will die soon."""
    msgs = {
        "ru": f"⚠️ <b>Внимание!</b> Твоя курица умрёт через {hours_left:.0f} часа!\nЗайди в игру и покорми её! 🐔",
        "en": f"⚠️ <b>Warning!</b> Your chicken will die in {hours_left:.0f} hours!\nOpen the game and feed her! 🐔",
        "zh": f"⚠️ <b>警告！</b>你的鸡将在{hours_left:.0f}小时内死亡！\n快去喂鸡！🐔",
    }
    msg = msgs.get(lang, msgs["en"])
    return await send_message(telegram_id, msg)


async def send_eggs_ready(telegram_id: int, eggs: int, lang: str = "ru") -> bool:
    """Notify player that eggs are ready to collect."""
    msgs = {
        "ru": f"🥚 Твои куры снесли яйца! Собери урожай!\n💰 Доступно: {eggs} яиц",
        "en": f"🥚 Your chickens laid eggs! Collect your harvest!\n💰 Available: {eggs} eggs",
        "zh": f"🥚 你的鸡下蛋了！去收集！\n💰 可用：{eggs}个蛋",
    }
    msg = msgs.get(lang, msgs["en"])
    return await send_message(telegram_id, msg)


async def send_low_feed_warning(telegram_id: int, bags_left: int, lang: str = "ru") -> bool:
    """Notify player that feed is running low."""
    msgs = {
        "ru": f"🌾 Корм заканчивается! Осталось {bags_left} мешок(ов).\nКупи корм в магазине или пригласи друга!",
        "en": f"🌾 Feed running low! Only {bags_left} bag(s) left.\nBuy feed at market or invite a friend!",
    }
    msg = msgs.get(lang, msgs["en"])
    return await send_message(telegram_id, msg)


async def send_trader_arrived(telegram_id: int, lang: str = "ru") -> bool:
    """Notify player that trader has arrived."""
    msgs = {
        "ru": "🧑‍🌾 <b>Торговец приехал на твою ферму!</b>\nЗайди и выбери: купить курицу со скидкой или вывести деньги! 💰",
        "en": "🧑‍🌾 <b>The trader has arrived at your farm!</b>\nLogin and choose: buy a discounted chicken or withdraw money! 💰",
    }
    msg = msgs.get(lang, msgs["en"])
    return await send_message(telegram_id, msg)


async def send_broadcast(telegram_ids: List[int], text: str, delay: float = 0.05) -> dict:
    """
    Send a message to many users with rate limiting.
    Returns { sent: N, failed: N }
    """
    sent = 0
    failed = 0
    for tid in telegram_ids:
        ok = await send_message(tid, text)
        if ok:
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(delay)  # Telegram rate limit: ~20/s
    return {"sent": sent, "failed": failed}


async def set_webhook(webhook_url: str) -> bool:
    """Register webhook URL with Telegram."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{TELEGRAM_API}/setWebhook", json={
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query", "pre_checkout_query", "successful_payment"],
            })
            data = resp.json()
            logger.info(f"Webhook set: {data}")
            return data.get("ok", False)
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return False


# ── Scheduled jobs (APScheduler integration) ──────────────────────────────────

async def run_death_warning_check():
    """Check all users approaching chicken death and notify them."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.models import User

    now = datetime.now(timezone.utc)
    warning_threshold = now - timedelta(hours=22)  # fed 22h ago = 2h left

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                and_(
                    User.last_fed_at <= warning_threshold,
                    User.last_fed_at > now - timedelta(hours=24),
                    User.is_blocked == False,
                )
            )
        )
        users = result.scalars().all()

        for user in users:
            if user.telegram_id:
                hours_left = 24 - ((now - user.last_fed_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600)
                await send_death_warning(user.telegram_id, max(0, hours_left), user.language)


async def run_trader_notifications():
    """Notify players when trader arrives (game day 11, 21, 31...)."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.models import User
    from app.services.game_service import should_trader_appear

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_blocked == False))
        users = result.scalars().all()

        for user in users:
            if should_trader_appear(user) and user.game_day % 10 == 1:  # only on arrival day
                if user.telegram_id:
                    await send_trader_arrived(user.telegram_id, user.language)


def setup_scheduler(app):
    """Attach APScheduler to FastAPI app."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(run_death_warning_check, "interval", minutes=30, id="death_check")
        scheduler.add_job(run_trader_notifications, "cron", hour=9, minute=0, id="trader_notify")
        scheduler.start()
        logger.info("APScheduler started")
        return scheduler
    except ImportError:
        logger.warning("APScheduler not installed, skipping scheduled jobs")
        return None
