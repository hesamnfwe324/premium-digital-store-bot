# 💳 Premium Digital Cards Marketplace — Telegram Bot

A world-class, production-ready Telegram e-commerce bot for selling Visa Cards, MasterCards, Virtual Cards, Gift Cards, and Digital Payment Services. Built with Aiogram 3.x, PostgreSQL, SQLAlchemy, and ready to deploy on Render.com.

---

## 🚀 Features

- 🌍 **8 Languages**: English, Spanish, French, German, Russian, Chinese, Arabic, Persian
- 💳 **Product Categories**: Visa Cards, MasterCards, Gift Cards, Premium Services
- 🔐 **Crypto Payments**: USDT TRC20/BEP20, BTC, ETH, BNB, TON — with QR codes
- 📦 **Auto Delivery**: Instant product delivery after payment confirmation
- 🎯 **Referral System**: Earn 5% from each purchase your referrals make
- 🎫 **Discount Codes**: Fixed and percentage discounts with expiry and usage limits
- 💰 **Internal Wallet**: Balance, deposits, earnings history
- 🎫 **Support Tickets**: Full ticket system with admin response
- 🔐 **Admin Panel**: Products, orders, payments, users, inventory, broadcast, analytics
- 📊 **Analytics**: Revenue (daily/weekly/monthly), user stats, referral stats
- 🚀 **Render Ready**: Webhook mode, health check endpoint, Docker support

---

## 📁 Project Structure

```
telegram-bot/
├── main.py                    # Bot entry point
├── config/
│   └── settings.py            # Pydantic settings
├── database/
│   ├── connection.py          # SQLAlchemy async engine
│   └── models/                # 14 database models
├── bot/
│   ├── handlers/              # Message & callback handlers
│   │   └── admin/             # Full admin panel handlers
│   ├── keyboards/             # Inline keyboards
│   ├── services/              # Business logic layer
│   ├── middlewares/           # Language, anti-spam, admin check
│   └── utils/                 # i18n, logger, QR code, helpers
├── locales/                   # 8 language JSON files
├── alembic/                   # Database migrations
├── requirements.txt
├── Dockerfile
├── render.yaml
└── .env.example
```

---

## ⚙️ Setup

### 1. Clone and Install

```bash
cd telegram-bot
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

**Required:**
- `BOT_TOKEN` — from @BotFather
- `DATABASE_URL` — PostgreSQL connection string
- `ADMIN_IDS` — comma-separated Telegram user IDs

**Crypto wallets:**
- `USDT_TRC20_ADDRESS`, `USDT_BEP20_ADDRESS`, `BTC_ADDRESS`, `ETH_ADDRESS`, `BNB_ADDRESS`, `TON_ADDRESS`

### 3. Initialize Database

```bash
alembic upgrade head
# OR (auto-creates tables without migrations)
python -c "import asyncio; from database.connection import init_db; asyncio.run(init_db())"
```

### 4. Run Locally (Polling)

```bash
WEBHOOK_ENABLED=false python main.py
```

---

## 🐳 Docker

```bash
docker build -t premium-digital-bot .
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  premium-digital-bot
```

---

## ☁️ Deploy to Render

### Step 1: Push to GitHub
Push this project to a GitHub repository.

### Step 2: Create Render Web Service
1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Render will auto-detect `render.yaml`

### Step 3: Set Environment Variables in Render Dashboard
Set these in **Environment** tab:
- `BOT_TOKEN` — your bot token
- `ADMIN_IDS` — your Telegram ID
- `WEBHOOK_HOST` — `https://your-app-name.onrender.com`
- All crypto wallet addresses

### Step 4: Set Webhook
After deployment, your webhook URL will be:
`https://your-app-name.onrender.com/webhook`

This is automatically set on startup when `WEBHOOK_ENABLED=true`.

### Step 5: Health Check
Render will monitor: `https://your-app-name.onrender.com/health`

---

## 🔐 Admin Panel

Send `/admin` in Telegram (only works for IDs in `ADMIN_IDS`).

**Admin features:**
- 📊 Dashboard with live stats
- 📦 Add/edit/delete products
- 📦 Inventory management (upload card codes)
- 🛒 Order management & manual delivery
- 💳 Payment confirmation/rejection
- 👥 User management (ban/unban, add balance)
- 🎫 Discount code management
- 📢 Broadcast messages to all users
- 📈 Full analytics dashboard

---

## 💳 Adding Inventory

**Gift Cards** (via Admin Panel → Inventory):
```
AMAZON_CODE_HERE
AMAZON_CODE_HERE|1234    ← with PIN
```

**Visa/MasterCards** (via Admin Panel → Inventory):
```
4111111111111111|12|2026|123|John Doe|123 Main St USA
```

---

## 💰 Payment Flow

1. User selects product → Bot creates order
2. User selects crypto → Bot shows wallet address + QR code
3. User sends payment → Copies TXID/link into bot
4. Admin gets notification → Confirms or rejects payment
5. On confirmation → Product auto-delivered from inventory
6. User receives product with professional status updates

---

## 🌍 Language System

Add new locales by creating `locales/XX.json` and registering in `bot/utils/i18n.py`.

---

## 🔒 Security

- Admin access controlled by `ADMIN_IDS` env var
- Anti-spam rate limiting (1s per message, 0.5s per callback)
- Input validation on all user inputs
- No secrets in code — all via environment variables
- Banned user check (extend in LanguageMiddleware)
- Production-grade logging with log rotation

---

## 📊 Database Schema

| Table | Purpose |
|-------|---------|
| `users` | User profiles, language, referral code |
| `products` | Product catalog with multi-lang support |
| `orders` | Order tracking with status history |
| `payments` | Crypto payment records |
| `wallets` | Internal wallet balances |
| `transactions` | Wallet transaction ledger |
| `gift_cards` | Gift card inventory |
| `visa_cards` | Visa card inventory |
| `master_cards` | MasterCard inventory |
| `tickets` | Support tickets |
| `referrals` | Referral relationships |
| `discount_codes` | Discount code management |
| `settings` | Bot configuration |
| `languages` | Language registry |

---

## 📞 Support

Configure your support Telegram username in `.env`:
```
SUPPORT_USERNAME=@your_support
```
