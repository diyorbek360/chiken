from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum, JSON, func
)
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timezone
import enum

from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

# --- Перечисления (Enums) ---

class UserRole(str, enum.Enum):
    player = "player"
    moderator = "moderator"
    analyst = "analyst"
    admin = "admin"

class WithdrawStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"

class EventType(str, enum.Enum):
    registered = "registered"
    first_feed = "first_feed"
    fed_chickens = "fed_chickens"
    chicken_died = "chicken_died"
    bought_item = "bought_item"
    eggs_collected = "eggs_collected"
    eggs_stolen = "eggs_stolen"
    steal_attempt = "steal_attempt"
    steal_blocked_dog = "steal_blocked_dog"
    trader_arrived = "trader_arrived"
    trader_chose_withdraw = "trader_chose_withdraw"
    trader_chose_chicken = "trader_chose_chicken"
    withdraw_requested = "withdraw_requested"
    withdraw_completed = "withdraw_completed"
    referral_activated = "referral_activated"
    ton_wallet_linked = "ton_wallet_linked"
    admin_gave_item = "admin_gave_item"
    admin_took_item = "admin_took_item"
    nickname_changed = "nickname_changed"
    deposit = "deposit"

# --- Модели ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(64), nullable=True)
    nickname = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    language = Column(String(8), default="ru")
    role = Column(Enum(UserRole), default=UserRole.player)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)

    # Игровые параметры
    game_day = Column(Integer, default=1)
    chickens = Column(Integer, default=1)
    super_chickens = Column(Integer, default=0)
    feed_bags = Column(Integer, default=0)
    eggs_collected = Column(Integer, default=0)
    balance_usd = Column(Float, default=0.0)
    balance_ton = Column(Float, default=0.0)

    # Предметы
    has_glove = Column(Boolean, default=False)
    has_dog = Column(Boolean, default=False)
    has_auto_feeder = Column(Boolean, default=False)

    # Состояние кормления
    last_fed_at = Column(DateTime(timezone=True), nullable=True)
    feeder_level = Column(Float, default=0.0)

    ton_wallet = Column(String(128), nullable=True)
    referral_code = Column(String(32), unique=True, nullable=True)

    # Торговец
    trader_day = Column(Integer, nullable=True)
    trader_last_seen = Column(Integer, nullable=True)

    # Обучение
    tutorial_completed = Column(Boolean, default=False)
    tutorial_market_done = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    last_active_at = Column(DateTime(timezone=True), default=utcnow)

    # Поле для реферальной системы
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Связи (Relationships)
    # Используем строки "User.id" и "User.referred_by_id", чтобы избежать NameError
    referrer = relationship(
        "User",
        remote_side="User.id",
        foreign_keys="[User.referred_by_id]",
        backref=backref("referred_users", lazy="dynamic"),
    )
    
    events = relationship("GameEvent", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    
    # Связи для записей о кражах (кто украл и у кого украли)
    steal_records_as_thief = relationship(
        "StealRecord", 
        foreign_keys="[StealRecord.thief_id]", 
        back_populates="thief"
    )
    steal_records_as_victim = relationship(
        "StealRecord", 
        foreign_keys="[StealRecord.victim_id]", 
        back_populates="victim"
    )


class GameEvent(Base):
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    user = relationship("User", back_populates="events")


class StealRecord(Base):
    """Записи о кражах яиц."""
    __tablename__ = "steal_records"

    id = Column(Integer, primary_key=True, index=True)
    thief_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    victim_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    eggs_amount = Column(Float, default=0.0)
    stolen_at = Column(DateTime(timezone=True), default=utcnow)

    thief = relationship("User", foreign_keys=[thief_id], back_populates="steal_records_as_thief")
    victim = relationship("User", foreign_keys=[victim_id], back_populates="steal_records_as_victim")


class Withdrawal(Base):
    """Запросы на вывод средств."""
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount_usd = Column(Float, nullable=False)
    ton_wallet = Column(String(128), nullable=False)
    status = Column(Enum(WithdrawStatus), default=WithdrawStatus.pending)
    admin_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="withdrawals")


class Transaction(Base):
    """Транзакции (депозиты, покупки, награды)."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(32), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="transactions")


class GameSettings(Base):
    """Настройки игры (редактируются через админку)."""
    __tablename__ = "game_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(String(512), nullable=False)
    value_type = Column(String(16), default="float")
    label = Column(String(128), nullable=True)
    category = Column(String(32), default="general")
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class Translation(Base):
    """Локализация фраз."""
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    phrase_key = Column(String(128), unique=True, nullable=False, index=True)
    ru = Column(Text, nullable=True)
    en = Column(Text, nullable=True)
    zh = Column(Text, nullable=True)
    hi = Column(Text, nullable=True)
    es = Column(Text, nullable=True)
    fr = Column(Text, nullable=True)
    ar = Column(Text, nullable=True)
    bn = Column(Text, nullable=True)
    pt = Column(Text, nullable=True)
    ur = Column(Text, nullable=True)


class AdminLog(Base):
    """Логи действий администратора."""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(128), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    """Уведомления и пуш-кампании."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    message_ru = Column(Text, nullable=True)
    message_en = Column(Text, nullable=True)
    audience = Column(String(32), default="all")
    audience_filter = Column(JSON, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    sent_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)