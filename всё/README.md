# 🐔 Golden Egg Farm — Telegram Mini App

## Архитектура проекта

```
golden-egg-farm/
├── frontend/               # Telegram Mini App (HTML/CSS/JS)
│   ├── index.html          # Главная страница (игра)
│   ├── css/
│   │   └── main.css        # Стили
│   ├── js/
│   │   ├── app.js          # Главный модуль
│   │   ├── api.js          # API-клиент
│   │   ├── game.js         # Игровая логика
│   │   ├── ui.js           # UI-компоненты
│   │   ├── i18n.js         # Мультиязычность
│   │   └── ton.js          # TON Connect
│   └── assets/             # Спрайты и изображения
│
├── backend/                # FastAPI backend
│   ├── main.py             # Точка входа
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/            # Миграции БД
│   └── app/
│       ├── core/
│       │   ├── config.py   # Настройки
│       │   ├── database.py # Подключение к PostgreSQL
│       │   └── security.py # Верификация Telegram
│       ├── models/
│       │   └── models.py   # SQLAlchemy модели
│       ├── api/
│       │   ├── router.py   # Все роуты
│       │   ├── game.py     # Игровые эндпоинты
│       │   ├── shop.py     # Магазин
│       │   ├── leaderboard.py
│       │   ├── referral.py
│       │   └── admin.py    # Админ-панель
│       └── services/
│           ├── game_service.py
│           ├── bot_service.py  # Telegram Bot
│           └── ton_service.py  # TON Connect
│
└── docs/
    └── API.md              # Документация API
```

## MVP функции (Phase 1)
- [x] Авторизация через Telegram WebApp
- [x] Курица и накопление яиц
- [x] Кормление раз в 24 часа
- [x] Базовый магазин (корм, улучшения)
- [x] Лидерборд (топ-100)
- [x] Реферальная система
- [x] Мультиязычность (10 языков)
- [x] Админ-панель (базовая)

## Phase 2 (расширение)
- [ ] Воровство яиц у других игроков
- [ ] Торговец каждые 10 дней
- [ ] TON Connect оплата
- [ ] Продвинутая аналитика
- [ ] Достижения и ивенты

## Запуск

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Заполнить .env
alembic upgrade head
uvicorn main:app --reload
```

### Frontend
```bash
# Просто открыть index.html или деплоить на CDN
# Для разработки:
npx serve frontend/
```

## Переменные окружения (.env)
```
DATABASE_URL=postgresql://user:pass@localhost/golden_egg_farm
TELEGRAM_BOT_TOKEN=your_bot_token
SECRET_KEY=your_secret_key
TON_NETWORK=mainnet
ADMIN_IDS=123456789,987654321
```
