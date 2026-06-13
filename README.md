# SwiftyPay Backend

Django REST API for the SwiftyPay Telegram Mini App — create shareable crypto payment links.

## Stack

- Django 5 + Django REST Framework
- PostgreSQL (Neon)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in values
python manage.py migrate
python manage.py runserver
```

Health check: `GET http://localhost:8000/health/`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/links/create` | Create a payment link |
| GET | `/api/links/:id` | Get link details |
| POST | `/api/links/:id/pay` | Mark link as paid + notify requester |
| GET | `/api/suggest-coin` | AI coin suggestion (CoinGecko + Groq) |

### POST /api/links/create

```json
{
  "amount": 10,
  "coin": "USDT",
  "note": "For logo design",
  "telegramUserId": "123456789",
  "telegramUsername": "abraham_dev",
  "initData": "<telegram-webapp-init-data>"
}
```

In `DEBUG` mode, empty `initData` is accepted with a debug user.

### Environment variables

See `.env.example`.
# swiftpay
