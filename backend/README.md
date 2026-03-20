# AurumCap — Backend

REST API for the AurumCap portfolio tracking platform, built with FastAPI and PostgreSQL.

## Tech Stack

| | |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy async + asyncpg |
| Caching | Redis |
| HTTP clients | `twelvedata` SDK, `massive` SDK, `httpx` (CoinMarketCap), `finnhub-python` |
| Auth | JWT (pyjwt) + bcrypt |
| Config | pydantic-settings |
| Containerization | Docker + Docker Compose |


## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- API keys for TwelveData, Massive, CoinMarketCap, and Finnhub

## Setup

**1. Clone and enter the backend directory**
```bash
git clone https://github.com/JuanHerDev/aurumcap.git
cd aurumcap/backend
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Open `.env` and fill in all required values (see table below).

**5. Start the database and Redis**
```bash
docker-compose up -d
```

**6. Start the development server**
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

**7. Seed the database (optional)**
```bash
python -m scripts.seed
```

Creates a test user and sample holdings:

| Credential | Value |
|---|---|
| Email | `test@aurumcap.com` |
| Password | `aurumcap123` |
| Holdings | BTC (0.5), AAPL (10), TSLA (5), AMZN (3), QQQ (8), NNE (50) |

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string — `postgresql+asyncpg://user:pass@host/db` |
| `TWELVEDATA_API_KEY` | TwelveData API key — live prices + historical data |
| `MASSIVE_API_KEY` | Massive (formerly Polygon) API key — stocks/ETFs metadata |
| `COINMARKETCAP_API_KEY` | CoinMarketCap API key — crypto prices + search |
| `FINNHUB_API_KEY` | Finnhub API key — company fundamentals |
| `REDIS_URL` | Redis connection string — `redis://localhost:6379` |
| `JWT_SECRET` | Secret key for signing JWT tokens |
| `APP_ENV` | `development` or `production` |
| `DEBUG` | `True` or `False` |

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Login and receive JWT token |

### Users
| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get current user profile |
| PUT | `/users/me` | Update profile |

### Market Data
| Method | Endpoint | Description |
|---|---|---|
| GET | `/price/{symbol}` | Live price for a stock, ETF, or crypto |
| GET | `/search?q={query}` | Asset search with autocomplete |
| GET | `/fundamentals/{symbol}` | Company fundamentals (stocks/ETFs only) |
| GET | `/market/status` | Current US market status |

### Assets
| Method | Endpoint | Description |
|---|---|---|
| GET | `/assets/resolve/{symbol}` | Resolve symbol to asset_id (creates if missing) |

### Portfolio
| Method | Endpoint | Description |
|---|---|---|
| GET | `/portfolio/me` | Current portfolio value + holdings with live prices |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| POST | `/transactions` | Record a BUY or SELL transaction |
| GET | `/transactions` | List all transactions |
| GET | `/transactions/{id}` | Get a single transaction |
| PUT | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |

### Watchlist
| Method | Endpoint | Description |
|---|---|---|
| GET | `/watchlist` | Get watchlist with live prices |
| POST | `/watchlist/{symbol}` | Add asset to watchlist |
| DELETE | `/watchlist/{symbol}` | Remove asset from watchlist |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/portfolio/history?range={range}` | Portfolio value over time |
| GET | `/analytics/portfolio/allocation` | Current asset allocation |

### Trading
| Method | Endpoint | Description |
|---|---|---|
| POST | `/trading` | Open a long/short trade |
| GET | `/trading` | List all trades |
| PUT | `/trading/{id}/close` | Close an open trade |

## Data Providers

| Provider | Used for | Rate limit | Cache TTL |
|---|---|---|---|
| TwelveData | Live prices, historical time series | 8 credits/min (free) | 30s (prices), 1h (history) |
| Massive | Stocks/ETFs metadata, market status | — | 60s (market status) |
| CoinMarketCap | Crypto prices, crypto search | — | 30s (prices) |
| Finnhub | Company fundamentals | — | 24h |

## Rate Limiting

TwelveData's free plan allows 8 API credits per minute. The backend implements a
token-bucket rate limiter (`app/core/rate_limiter.py`) that queues requests rather
than failing with 429 errors. This means:

- Portfolio loads may take 3–7 seconds on cache miss (stocks fetched sequentially)
- Analytics history loads may take 1–3 minutes on first load (6 holdings × ~10s each)
- All subsequent loads within the cache window are instant

## Caching Strategy

| Data | TTL | Reason |
|---|---|---|
| Live prices | 30s | Balance freshness vs API credits |
| Portfolio | 5 min | Expensive to compute — sequential price fetches |
| Market status | 60s | Changes at most twice per day |
| Search results | 5 min | Stable — assets don't rename frequently |
| Fundamentals | 24h | Changes quarterly at most |
| History / allocation | 1h | Historical prices are immutable |

## Project Structure
```
backend/
├── app/
│   ├── core/
│   │   ├── settings.py          # Environment config (pydantic-settings)
│   │   ├── cache.py             # Redis helpers + TTL constants
│   │   ├── rate_limiter.py      # Token bucket limiter for TwelveData (6 req/min)
│   │   └── dependencies.py      # get_current_user — JWT auth dependency
│   ├── db/
│   │   ├── base_class.py        # SQLAlchemy DeclarativeBase
│   │   ├── base.py              # Imports all models (for Alembic)
│   │   ├── session.py           # AsyncEngine + AsyncSessionLocal + get_db
│   │   └── init_db.py           # Async DB initialization
│   ├── models/
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
│   ├── providers/
│   │   ├── massive_provider.py          # Stocks/ETFs metadata + market status
│   │   ├── coinmarketcap_provider.py    # Crypto prices + search (httpx async)
│   │   ├── finnhub_provider.py          # Fundamentals (P/E, ROE, Beta, etc.)
│   │   └── twelvedata_provider.py       # Live prices + historical time series
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── assets.py
│   │   ├── price.py
│   │   ├── search.py
│   │   ├── fundamentals.py
│   │   ├── portfolio.py
│   │   ├── transactions.py
│   │   ├── analytics.py
│   │   ├── watchlist.py
│   │   ├── trading.py
│   │   └── market.py
│   ├── services/
│   │   ├── auth_service.py          # bcrypt + JWT token creation/validation
│   │   ├── user_service.py          # CRUD user profile
│   │   ├── asset_service.py         # get_or_create_asset (cache-aside)
│   │   ├── price_service.py         # Live price with Redis cache (30s TTL)
│   │   ├── search_service.py        # DB first → external providers + cache (5min)
│   │   ├── market_service.py        # Market status + cache (60s)
│   │   ├── fundamentals_service.py  # Finnhub fundamentals + cache (24h)
│   │   ├── portfolio_service.py     # Holdings with live prices + cache (5min)
│   │   ├── transaction_service.py   # BUY/SELL with weighted avg price
│   │   ├── trading_service.py       # Long/short trades + P&L
│   │   ├── watchlist_service.py     # CRUD watchlist with live prices
│   │   └── analytics_service.py     # History + allocation + cache (1h/5min)
│   ├── routes/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── assets.py
│   │   ├── price.py
│   │   ├── search.py
│   │   ├── fundamentals.py
│   │   ├── market.py
│   │   ├── portfolio.py
│   │   ├── transactions.py
│   │   ├── trading.py
│   │   ├── watchlist.py
│   │   └── analytics.py
│   └── main.py                      # FastAPI app — CORS, lifespan, routers
├── scripts/
│   └── seed.py                      # Seed DB with test user + holdings
├── alembic/                         # Database migrations
├── .env.example
├── docker-compose.yml
└── requirements.txt
```

## License

MIT