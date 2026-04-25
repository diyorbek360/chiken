from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/golden_egg_farm"
    TELEGRAM_BOT_TOKEN: str = ""
    SECRET_KEY: str = "change-me-in-production"
    ADMIN_IDS: str = ""
    TON_NETWORK: str = "testnet"
    TON_MANIFEST_URL: str = "https://yourdomain.com/tonconnect-manifest.json"
    WEBHOOK_URL: str = ""
    DEBUG: bool = True

    EGG_VALUE_USD: float = 0.20          
    FEED_COST_USD: float = 0.18        
    CHICKEN_COST_USD: float = 1.0
    GLOVE_COST_USD: float = 2.0
    SUPER_CHICKEN_COST_USD: float = 3.0
    DOG_COST_USD: float = 5.0
    AUTO_FEEDER_COST_PERCENT: float = 3.0 
    STEAL_PERCENT: float = 10.0
    TRADER_INTERVAL_DAYS: int = 10
    TRADER_DISCOUNT_PERCENT: float = 20.0
    FEED_DEATH_HOURS: int = 24
    DEATH_WARNING_HOURS: int = 2
    REFERRAL_FEED_BONUS: int = 3        
    REFERRAL_FEED_NORMAL: int = 1
    MAX_CHICKENS_VISUAL: int = 10
    REDIS_URL: str = "redis://redis:6379"

    @property
    def admin_id_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
