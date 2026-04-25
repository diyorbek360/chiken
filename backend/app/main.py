from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.router import router as game_router
from app.api.admin import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Golden Egg Farm backend...")
    await init_db()
    await seed_default_data()
    logger.info("Database ready!")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Golden Egg Farm API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


async def seed_default_data():
    """Insert default translations and game settings if missing."""
    from app.core.database import AsyncSessionLocal
    from app.models.models import Translation

    default_phrases = [
        ("welcome_title", "Добро пожаловать!", "Welcome!", "欢迎！"),
        ("feed_btn", "Покормить", "Feed", "喂食"),
        ("collect_btn", "Собрать яйца", "Collect Eggs", "收集鸡蛋"),
        ("market_title", "Рынок", "Market", "市场"),
        ("leaders_title", "Лидеры", "Leaders", "排行榜"),
        ("settings_title", "Настройки", "Settings", "设置"),
        ("day_label", "День", "Day", "天"),
        ("no_feed_error", "Нет корма! Купите в магазине.", "No feed! Buy at market.", "没有饲料！"),
        ("chicken_died_title", "Курица умерла 😢", "Chicken died 😢", "鸡死了 😢"),
        ("chicken_died_body", "Ваша курица умерла от голода. Вы можете начать снова!", "Your chicken died of hunger. You can start over!", "你的鸡饿死了。你可以重新开始！"),
        ("restart_btn", "Начать заново", "Start Over", "重新开始"),
        ("trader_title", "Торговец прибыл!", "Trader arrived!", "商人到来！"),
        ("trader_offer", "Выберите предложение:", "Choose an offer:", "选择提议："),
        ("buy_chicken_discount", "Купить курицу со скидкой", "Buy chicken with discount", "折扣购买鸡"),
        ("withdraw_money", "Вывести деньги", "Withdraw money", "提款"),
        ("no_glove_popup", "У вас нет перчатки вора. Купите её в магазине!", "You don't have thief gloves. Buy them at market!", "你没有小偷手套。去市场购买！"),
        ("dog_protection", "Собака охраняет этот двор! Ничего украсть нельзя.", "Dog guards this farm! Can't steal anything.", "狗守护着这个农场！无法偷窃。"),
        ("already_stolen", "Яйца уже были украдены сегодня. Приходи завтра!", "Eggs were already stolen today. Come back tomorrow!", "今天的蛋已经被偷了。明天再来！"),
        ("tutorial_1", "Твоя курица несёт золотые яйца! 🐔", "Your chicken lays golden eggs! 🐔", "你的鸡下金蛋！🐔"),
        ("tutorial_2", "Кормушка — корми курицу каждые 24 часа!", "Feeder — feed your chicken every 24 hours!", "喂食器 — 每24小时喂一次鸡！"),
        ("tutorial_3", "Следи за запасом корма. Его можно купить или получить за друзей!", "Watch your feed supply. Buy it or earn it for friends!", "注意饲料供应。可以购买或邀请朋友获得！"),
        ("tutorial_4", "В магазине — корм, куры и улучшения для фермы!", "At the market — feed, chickens and upgrades!", "市场里有饲料、鸡和升级！"),
        ("tutorial_5", "Осторожно! Другие игроки могут украсть яйца. Купи собаку для защиты!", "Careful! Others can steal eggs. Buy a dog for protection!", "小心！其他玩家可以偷蛋。买只狗来保护！"),
        ("tutorial_6", "Каждые 10 дней приезжает торговец. Продай яйца или купи курицу!", "Trader comes every 10 days. Sell eggs or buy a chicken!", "每10天商人来一次。卖蛋或买鸡！"),
        ("days_until_trader", "До торговца {days} дн.", "Trader in {days} days", "{days}天后商人来"),
        ("wallet_saved", "Кошелёк сохранён!", "Wallet saved!", "钱包已保存！"),
        ("no_wallet", "Привяжите TON кошелёк в настройках для вывода.", "Link TON wallet in settings to withdraw.", "在设置中绑定TON钱包以提款。"),
        ("withdraw_pending", "Запрос на вывод принят. Статус — в настройках.", "Withdrawal request accepted. Status in settings.", "提款请求已接受。状态在设置中。"),
        ("invite_msg", "Моя курица несёт золотые яйца 🐔 Заведи свою! {link}", "My chicken lays golden eggs 🐔 Get yours! {link}", "我的鸡下金蛋🐔 快来养一只！{link}"),
        ("death_warning", "⚠️ Осталось 2 часа до смерти курицы! Покорми её!", "⚠️ 2 hours until chicken dies! Feed her!", "⚠️ 距离鸡死亡还有2小时！快喂食！"),
        ("low_feed_warning", "🛒 Корм заканчивается! Остался 1 мешок.", "🛒 Feed running low! 1 bag left.", "🛒 饲料不多了！只剩1袋。"),
    ]

    async with AsyncSessionLocal() as db:
        for key, ru, en, zh in default_phrases:
            result = await db.execute(
                __import__("sqlalchemy", fromlist=["select"]).select(Translation).where(Translation.phrase_key == key)
            )
            if not result.scalar_one_or_none():
                t = Translation(phrase_key=key, ru=ru, en=en, zh=zh)
                db.add(t)
        await db.commit()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
