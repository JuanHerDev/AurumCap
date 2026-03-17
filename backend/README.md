# AurumCap — Backend

REST API for the AurumCap portfolio tracking platform, built with FastAPI and PostgreSQL.

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL + SQLAlchemy (async) + Alembic
- **HTTP clients**: `massive` SDK (stocks/ETFs), `httpx` (CoinMarketCap), `finnhub-python`
- **Config**: pydantic-settings
- **Containerization**: Docker + Docker Compose

## Project Structure
```
backend/
├── app/
│   ├── core/
│   │   └── settings.py         # Environment config (pydantic-settings)
│   ├── db/
│   │   ├── base.py             # SQLAlchemy declarative base
│   │   ├── session.py          # DB engine and session factory
│   │   └── init_db.py          # DB initialization
│   ├── models/                 # SQLAlchemy models
│   │   ├── asset.py
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── holdings.py
│   │   ├── trade.py
│   │   ├── price_history.py
│   │   ├── portfolio_snapshot.py
│   │   ├── platform.py
│   │   ├── news.py
│   │   └── watchlist.py
│   ├── providers/              # External API integrations
│   │   ├── massive_provider.py         # Stocks + ETFs (Massive/Polygon)
│   │   ├── coinmarketcap_provider.py   # Crypto (CoinMarketCap)
│   │   └── finnhub_provider.py         # Fundamentals (Finnhub)
│   ├── routes/                 # API endpoints (coming soon)
│   └── main.py                 # FastAPI app entrypoint
├── alembic/                    # Database migrations
├── .env.example                # Environment variables template
├── docker-compose.yml
└── requirements.txt
```

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- API keys for [Massive](https://massive.com), [CoinMarketCap](https://coinmarketcap.com/api), and [Finnhub](https://finnhub.io)

## Setup

**1. Clone and enter the backend directory**
```bash
git clone https://github.com/JuanHerDev/aurumcap.git
cd aurumcap/backend
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Then open `.env` and fill in your API keys and database credentials.

**5. Start the database**
```bash
docker-compose up -d
```

**6. Run migrations**
```bash
alembic upgrade head
```

**7. Start the development server**
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `MASSIVE_API_KEY` | Massive (Polygon) API key |
| `COINMARKETCAP_API_KEY` | CoinMarketCap API key |
| `FINNHUB_API_KEY` | Finnhub API key |
| `REDIS_URL` | Redis connection string |
| `APP_ENV` | `development` or `production` |
| `DEBUG` | `True` or `False` |

## API Endpoints

> Work in progress — endpoints will be documented here as they are implemented.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/price/{symbol}` | Current price for a stock, ETF, or crypto |
| GET | `/search?q={query}` | Asset search with autocomplete |
| GET | `/fundamentals/{symbol}` | Company fundamentals |
| GET | `/market/status` | Current market status |
| GET | `/portfolio/{user_id}` | Portfolio value and holdings |

## Data Providers

| Provider | Assets | SDK |
|---|---|---|
| [Massive](https://massive.com) (formerly Polygon.io) | Stocks, ETFs | `massive` |
| [CoinMarketCap](https://coinmarketcap.com/api) | Crypto | `httpx` (no official SDK) |
| [Finnhub](https://finnhub.io) | Fundamentals, news | `finnhub-python` |

## Roadmap

- [ ] Pydantic schemas (request/response validation)
- [ ] Services layer (price, search, portfolio, fundamentals)
- [ ] API routers
- [ ] Redis caching
- [ ] Background jobs (Celery) for price updates
- [ ] Authentication (JWT)

## License

MIT