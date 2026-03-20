Dependencias:

tailwindcss @tailwindcss/vite
recharts
react-router-dom
axios
lucide-react
zustand

Estructura:

src/
├── api/
│   └── client.js          # axios instance + interceptors
├── components/
│   ├── ui/                # botones, badges, cards reutilizables
│   ├── charts/            # componentes de gráficos
│   └── layout/            # sidebar, navbar, bottom nav
├── pages/
│   ├── Dashboard.jsx
│   ├── Portfolio.jsx
│   ├── Search.jsx
│   ├── AssetDetail.jsx
│   ├── Analytics.jsx
│   ├── Watchlist.jsx
│   ├── Trading.jsx
│   └── Auth.jsx
├── hooks/
│   └── useTheme.js        # dark/light toggle
├── store/
│   └── authStore.js       # zustand para auth state
└── utils/
    └── formatters.js      # formatear precios, porcentajes, fechas