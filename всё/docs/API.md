# Golden Egg Farm — API Documentation

## Base URL
- Dev: `http://localhost:8000/api/v1`
- Prod: `https://yourdomain.com/api/v1`

## Authentication
All game endpoints require `X-Init-Data` header with Telegram WebApp initData.

**Dev mode** (DEBUG=true): `X-Init-Data: debug:TELEGRAM_USER_ID`

---

## Game Endpoints

### POST /auth/init
Initialize player session. Call on every app open.

**Body:**
```json
{
  "telegram_id": 123456789,
  "username": "player_nick",
  "language": "ru",
  "referral_code": "ABC12345"
}
```

**Response:**
```json
{
  "user": { ...full user state... },
  "is_new": false,
  "chicken_alive": { "alive": true, "hours_remaining": 18.5, "warning": false }
}
```

### GET /me
Get current user state (authenticated).

### POST /game/feed
Feed chickens (uses 1 feed bag per chicken).

**Response:**
```json
{
  "success": true,
  "bags_used": 1,
  "remaining_bags": 2,
  "feeder_level": 1.0,
  "is_first_feed": false
}
```

### POST /game/collect
Collect accumulated eggs from tray.

### POST /game/steal
Steal eggs from another player.

**Body:** `{ "victim_user_id": 42 }`

**Response reasons:**
- `no_glove` — player doesn't have thief gloves
- `dog_protection` — victim has guard dog
- `already_stolen_today` — victim already robbed today
- `cannot_steal_self` — can't steal from yourself

### POST /shop/buy
Purchase item from shop.

**Body:** `{ "item": "feed", "quantity": 3 }`

**Items:** `chicken`, `feed`, `glove`, `dog`, `super_chicken`, `auto_feeder`

### GET /shop/prices
Get current shop prices (from admin-configurable settings).

### GET /leaderboard
Top 100 players by balance.

### GET /leaderboard/player/{id}
View another player's farm (for theft mechanic).

### PATCH /settings/nickname
### PATCH /settings/wallet
### PATCH /settings/language
### GET /settings/referrals

### POST /withdraw/request
Request money withdrawal.

**Body:** `{ "amount": 10.5 }`

### GET /withdraw/history

---

## Admin Endpoints (require admin Telegram ID)

### GET /admin/dashboard
Full game statistics.

### GET /admin/players?page=1&limit=50&search=...
### GET /admin/players/{id}
### PATCH /admin/players/{id}
### POST /admin/players/{id}/give

**Body:** `{ "item": "feed", "quantity": 10, "reason": "Support gift" }`

### GET /admin/withdrawals?status=pending
### PATCH /admin/withdrawals/{id}

**Body:** `{ "action": "approve|reject|complete", "comment": "..." }`

### GET /admin/settings
### GET /admin/translations
### PATCH /admin/translations

**Body:** `{ "phrase_key": "welcome_title", "lang": "en", "text": "Welcome!" }`

---

## User State Object

```json
{
  "id": 1,
  "telegram_id": 123456789,
  "nickname": "FarmKing",
  "language": "ru",
  "game_day": 7,
  "chickens": 3,
  "super_chickens": 1,
  "feed_bags": 5,
  "eggs_collected": 42,
  "balance_usd": 8.40,
  "balance_ton": 0.0,
  "has_glove": false,
  "has_dog": true,
  "has_auto_feeder": false,
  "feeder_level": 0.65,
  "last_fed_at": "2026-04-15T10:30:00Z",
  "ton_wallet": null,
  "referral_code": "FARM1234",
  "tutorial_completed": true,
  "trader_active": false,
  "days_until_trader": 3
}
```

---

## Economy Reference

| Item | Default Price | Notes |
|------|--------------|-------|
| Egg income | $0.20/day/chicken | Configurable |
| Feed bag | $0.18 | ~10% less than egg income |
| Extra chicken | $1.00 | |
| Thief gloves | $2.00 | One-time |
| Guard dog | $5.00 | One-time |
| Super chicken | $3.00 | 2x egg production |
| Auto feeder | 3% of balance | One-time |
| Referral bonus | 3 feed bags | Early bird multiplier |
| Steal amount | 10% daily yield | One per victim per day |
| Trader discount | 20% off | Every 10 days |
