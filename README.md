# AurumCap

A professional portfolio tracking platform for stocks, ETFs, and cryptocurrencies — inspired by Delta, Yahoo Finance, and TradingView.

AurumCap lets users track their investments across multiple asset classes, analyze historical performance, and visualize portfolio growth over time.

## Features

- Real-time prices for stocks, ETFs, and crypto
- Historical portfolio value charts
- Asset search with autocomplete (Bloomberg/TradingView-style)
- Company fundamentals (P/E, ROE, margins, dividends)
- Market status detection (pre-market, open, after-hours, closed)
- Multi-platform transaction tracking

## Project Structure
```
aurumcap/
├── backend/     # FastAPI REST API
└── README.md
```

> Frontend coming soon.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, PostgreSQL, SQLAlchemy, Docker |
| Data providers | Massive (stocks/ETFs), CoinMarketCap (crypto), Finnhub (fundamentals) |
| Infrastructure | Redis (caching), Alembic (migrations), Celery (background jobs) |

## Getting Started

See the [backend README](./backend/README.md) for setup instructions.

## License

MIT