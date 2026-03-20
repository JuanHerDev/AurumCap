# AurumCap

A professional portfolio tracking platform for stocks, ETFs, and cryptocurrencies — inspired by Delta, Yahoo Finance, and TradingView.

AurumCap lets users track their investments across multiple asset classes, analyze historical performance, and visualize portfolio growth over time.

## Features

- Real-time prices for stocks, ETFs, and crypto
- Portfolio value history charts with configurable date ranges (1W, 1M, 3M, 1Y, ALL)
- Asset search with debounced autocomplete
- Company fundamentals — P/E, P/B, ROE, Net Margin, Beta, Dividend Yield, 52W range
- Crypto stats — Market Cap, 24h Volume, 7d Change
- Watchlist with live prices
- Buy/Sell transactions with average cost tracking
- Asset allocation breakdown (donut chart + progress bars)
- Market status detection (open / closed)
- Dark mode by default with light mode toggle
- Fully responsive — desktop sidebar + mobile bottom nav

## Project Structure
```
aurumcap/
├── backend/         # FastAPI REST API
├── frontend/        # React + Vite SPA
└── README.md
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, PostgreSQL, SQLAlchemy async, Alembic |
| Frontend | React 18, Vite, Tailwind CSS v4, Recharts, Zustand |
| Data providers | Massive (stocks/ETFs), CoinMarketCap (crypto), Finnhub (fundamentals), TwelveData (prices + history) |
| Infrastructure | Redis (caching + rate limiting), Docker Compose |

## Architecture notes

- **Rate limiting** — TwelveData free plan allows 8 credits/min. The backend implements a token-bucket rate limiter that queues requests rather than failing.
- **Caching** — Redis caches portfolio data (5 min), historical prices (1h), fundamentals (24h), and search results (5 min) to minimize API calls.
- **Sequential fetching** — Stock/ETF prices are fetched sequentially with the rate limiter; crypto is fetched in parallel via CoinMarketCap.

## Getting Started

See the individual READMEs for setup:

- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)

## License

MIT