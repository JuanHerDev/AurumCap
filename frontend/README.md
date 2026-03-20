# AurumCap — Frontend

React + Vite SPA for the AurumCap portfolio tracker.

## Tech Stack

| | |
|---|---|
| Framework | React 18 |
| Build tool | Vite |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) |
| Charts | Recharts |
| State management | Zustand |
| Routing | React Router v7 |
| HTTP client | Axios |
| Icons | Lucide React |


## Prerequisites

- Node.js 18+
- Backend running on `http://localhost:8000`

## Setup
```bash
cd frontend
npm install
```

Create a `.env` file (optional — defaults to `http://127.0.0.1:8000`):
```env
VITE_API_URL=http://127.0.0.1:8000
```

## Running
```bash
npm run dev
# → http://localhost:5173
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000` | Backend API base URL |

## API Clients

Two Axios instances are exported from `src/api/client.js`:

- **`client`** (default export) — 60s timeout, used for all standard endpoints
- **`analyticsClient`** (named export) — 5 min timeout, used for `/analytics/*` endpoints that may queue behind the TwelveData rate limiter

Both automatically attach the JWT token from `localStorage` and redirect to `/auth` on 401.

## Pages Overview

| Page | Route | Description |
|---|---|---|
| Auth | `/auth` | Login and registration |
| Dashboard | `/` | Portfolio value, stats, holdings preview |
| Portfolio | `/portfolio` | Full allocation chart and holdings table |
| Search | `/search` | Asset search across stocks, ETFs, crypto |
| Asset Detail | `/asset/:symbol` | Price, fundamentals, watchlist toggle |
| Analytics | `/analytics` | Historical chart and allocation breakdown |
| Watchlist | `/watchlist` | Saved assets with live prices |
| Trading | `/trading` | Buy and sell transactions |

## Design System

CSS variables defined in `src/index.css`:

| Variable | Value | Usage |
|---|---|---|
| `--gold` | `#F5C842` | Primary accent, active states |
| `--green` | `#00C896` | Positive values, gains |
| `--red` | `#FF4D6A` | Negative values, losses |
| `--bg-primary` | `#0A0F1E` | Page background |
| `--bg-card` | `#111827` | Card backgrounds |
| `--bg-tertiary` | `#1F2937` | Input backgrounds, chips |

Dark mode is default. Light mode adds the `.light` class to `<html>` and overrides all CSS variables.

## Known Limitations

- TwelveData free plan (8 credits/min) causes Analytics to take 2–3 minutes on first load. Subsequent loads are instant (cached for 1h in Redis).
- Asset Detail price may show "unavailable" if the rate limiter is busy from a concurrent Portfolio or Analytics load.
- Search only returns assets already in the database unless the backend fetches from external providers (Massive, CMC).

## Project Structure
```
frontend/
├── public/
├── src/
│   ├── api/
│   │   └── client.js          # Axios instances — standard (60s) + analytics (5min)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.jsx     # App shell — sidebar + topbar + bottom nav
│   │   │   ├── Sidebar.jsx    # Desktop navigation
│   │   │   ├── TopBar.jsx     # Mobile header
│   │   │   └── BottomNav.jsx  # Mobile tab bar
│   │   └── ui/
│   │       ├── Card.jsx       # Base card container
│   │       ├── Badge.jsx      # Positive/negative percentage badge
│   │       └── Skeleton.jsx   # Loading placeholder
│   ├── hooks/
│   │   └── useTheme.js        # Dark/light mode toggle with localStorage
│   ├── pages/
│   │   ├── Auth.jsx           # Login + Register tabs
│   │   ├── Dashboard.jsx      # Portfolio overview + holdings list
│   │   ├── Portfolio.jsx      # Donut chart + allocation + full holdings table
│   │   ├── Search.jsx         # Asset search with debounce (400ms)
│   │   ├── AssetDetail.jsx    # Price, OHLCV/crypto stats, fundamentals, watchlist
│   │   ├── Analytics.jsx      # Portfolio history chart + allocation bars
│   │   ├── Watchlist.jsx      # Saved assets with live prices
│   │   └── Trading.jsx        # Buy/Sell order form
│   ├── store/
│   │   └── authStore.js       # Zustand — login, register, logout, fetchUser
│   └── utils/
│       └── formatters.js      # formatCurrency, formatPercent, colorClass, etc.
├── index.html
├── package.json
└── vite.config.js
```

## License

MIT