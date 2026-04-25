

```
golden-egg-farm/
├── frontend/       
│   ├── index.html  
│   ├── css/
│   │   └── main.css
│   ├── js/
│   │   ├── app.js  
│   │   ├── api.js  
│   │   ├── game.js 
│   │   ├── ui.js   
│   │   ├── i18n.js 
│   │   └── ton.js  
│   └── assets/     
│
├── backend/        
│   ├── main.py     
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/    
│   └── app/
│       ├── core/
│       │   ├── config.py   
│       │   ├── database.py 
│       │   └── security.py 
│       ├── models/
│       │   └── models.py   
│       ├── api/
│       │   ├── router.py   
│       │   ├── game.py     
│       │   ├── shop.py     
│       │   ├── leaderboard.py
│       │   ├── referral.py
│       │   └── admin.py   
│       └── services/
│           ├── game_service.py
│           ├── bot_service.py 
│           └── ton_service.py
│
└── docs/
    └── API.md             
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
alembic upgrade head
uvicorn main:app --reload
```

### Frontend
```bash
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
