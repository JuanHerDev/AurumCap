/**
 * API Endpoints Configuration
 * Centralized configuration for all backend endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    REFRESH: `${API_BASE_URL}/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    ME: `${API_BASE_URL}/users/me`,
    CHANGE_PASSWORD: `${API_BASE_URL}/auth/me/password`,
  },

  // Portfolio endpoints (v1)
  PORTFOLIO: {
    BASE: `${API_BASE_URL}/portfolio`,
    INVESTMENTS: `${API_BASE_URL}/portfolio/investments`,
    INVESTMENT_CARDS: `${API_BASE_URL}/portfolio/investment-cards`,
    INVESTMENT_DETAIL: (id: number) => `${API_BASE_URL}/portfolio/investment-detail/${id}`,
    ALLOCATIONS: `${API_BASE_URL}/portfolio/analytics/allocations`,
    PERFORMANCE: `${API_BASE_URL}/portfolio/analytics/performance`,
    SPARKLINE: (symbol: string) => `${API_BASE_URL}/portfolio/sparkline/${symbol}`,
    
    // Transactions
    ADD_TRANSACTION: (id: number) => `${API_BASE_URL}/portfolio/investments/${id}/transactions`,
  },

  // Portfolio advanced endpoints
  PORTFOLIO_ADVANCED: {
    BASE: `${API_BASE_URL}/portfolio/advanced`,
    RISK_PROFILE: `${API_BASE_URL}/portfolio/advanced/risk-profile`,
    CURRENT_ALLOCATION: `${API_BASE_URL}/portfolio/advanced/allocation/current`,
    REBALANCING_RECOMMENDATIONS: `${API_BASE_URL}/portfolio/advanced/rebalancing/recommendations`,
    SELL_CALCULATOR: {
      PROFITS_ONLY: `${API_BASE_URL}/portfolio/advanced/sell-calculator/profits-only`,
      PERCENTAGE: `${API_BASE_URL}/portfolio/advanced/sell-calculator/percentage`,
    },
    DIVIDENDS: {
      BASE: `${API_BASE_URL}/portfolio/advanced/dividends`,
      SUMMARY: `${API_BASE_URL}/portfolio/advanced/dividends/summary`,
    },
    GOALS: {
      BASE: `${API_BASE_URL}/portfolio/advanced/goals`,
      DETAIL: (id: number) => `${API_BASE_URL}/portfolio/advanced/goals/${id}`,
      PROJECTION: (id: number) => `${API_BASE_URL}/portfolio/advanced/goals/${id}/projection`,
      CONTRIBUTE: (id: number) => `${API_BASE_URL}/portfolio/advanced/goals/${id}/contribute`,
      ALERTS: `${API_BASE_URL}/portfolio/advanced/goals/alerts/check`,
    },
    HEALTH_SCORE: `${API_BASE_URL}/portfolio/advanced/health-score`,
    ALERTS: {
      BASE: `${API_BASE_URL}/portfolio/advanced/alerts`,
      TRIGGER: (id: number) => `${API_BASE_URL}/portfolio/advanced/alerts/${id}/trigger`,
    },
    DASHBOARD: `${API_BASE_URL}/portfolio/advanced/dashboard`,
  },

  // Crypto endpoints (v1)
  CRYPTO_V1: {
    BASE: `${API_BASE_URL}/crypto`,
    PRICE: (symbol: string) => `${API_BASE_URL}/crypto/price/${symbol}`,
    PROFILE: (symbol: string) => `${API_BASE_URL}/crypto/profile/${symbol}`,
    MARKET_DATA: (symbol: string) => `${API_BASE_URL}/crypto/market-data/${symbol}`,
    HISTORICAL: (symbol: string) => `${API_BASE_URL}/crypto/historical/${symbol}`,
    GLOBAL_MARKET: `${API_BASE_URL}/crypto/global/market`,
    SEARCH: `${API_BASE_URL}/crypto/search`,
    TRENDING: `${API_BASE_URL}/crypto/trending`,
  },

  // Crypto enhanced endpoints (v2)
  CRYPTO_V2: {
    BASE: `${API_BASE_URL}/crypto/v2`,
    UNIVERSAL_SEARCH: `${API_BASE_URL}/crypto/v2/universal-search`,
    ANY_CRYPTO: (identifier: string) => `${API_BASE_URL}/crypto/v2/any/${identifier}`,
    AUTO_UPDATE: {
      STATUS: `${API_BASE_URL}/crypto/v2/auto-update/status`,
      FORCE: `${API_BASE_URL}/crypto/v2/auto-update/force`,
    },
    PRICES_CACHED: `${API_BASE_URL}/crypto/v2/prices/cached`,
    DISCOVER: {
      TRENDING: `${API_BASE_URL}/crypto/v2/discover/trending`,
      CATEGORIES: `${API_BASE_URL}/crypto/v2/discover/categories`,
    },
  },

  // Stocks endpoints
  STOCKS: {
    BASE: `${API_BASE_URL}/stocks`,
    PRICE: (symbol: string) => `${API_BASE_URL}/stocks/price/${symbol}`,
    PROFILE: (symbol: string) => `${API_BASE_URL}/stocks/profile/${symbol}`,
    QUOTE: (symbol: string) => `${API_BASE_URL}/stocks/quote/${symbol}`,
    HISTORICAL: (symbol: string) => `${API_BASE_URL}/stocks/historical/${symbol}`,
    FUNDAMENTALS: (symbol: string) => `${API_BASE_URL}/stocks/fundamentals/${symbol}`,
    SEARCH: `${API_BASE_URL}/stocks/search`,
    MARKET_STATUS: `${API_BASE_URL}/stocks/market/status`,
    PRICES_BATCH: `${API_BASE_URL}/stocks/prices/batch`,
    EXCHANGES: `${API_BASE_URL}/stocks/exchanges`,
    SECTORS: `${API_BASE_URL}/stocks/sectors`,
    CACHE_REFRESH: (symbol: string) => `${API_BASE_URL}/stocks/cache/refresh/${symbol}`,
  },

  // Fundamentals endpoints
  FUNDAMENTALS: {
    BASE: `${API_BASE_URL}/fundamentals`,
    CURRENT: (symbol: string) => `${API_BASE_URL}/fundamentals/current/${symbol}`,
    HISTORICAL: (symbol: string) => `${API_BASE_URL}/fundamentals/historical/${symbol}`,
    SECTOR: (sector: string) => `${API_BASE_URL}/fundamentals/sector/${sector}`,
    CALENDAR: {
      ECONOMIC: `${API_BASE_URL}/fundamentals/calendar/economic`,
      EARNINGS: `${API_BASE_URL}/fundamentals/calendar/earnings`,
      UPCOMING: `${API_BASE_URL}/fundamentals/calendar/upcoming`,
    },
    SECTORS_ALL: `${API_BASE_URL}/fundamentals/sectors/all`,
  },

  // Platforms endpoints
  PLATFORMS: {
    BASE: `${API_BASE_URL}/platforms`,
    BY_ASSET_TYPE: (assetType: string) => `${API_BASE_URL}/platforms/by-asset-type/${assetType}`,
    STATS: `${API_BASE_URL}/platforms/stats`,
    SEED_DEFAULTS: `${API_BASE_URL}/platforms/seed-defaults`,
    DETAIL: (id: number) => `${API_BASE_URL}/platforms/${id}`,
  },

  // Debug endpoints
  DEBUG: {
    CRYPTO_PRICE: (symbol: string) => `${API_BASE_URL}/debug/crypto-price/${symbol}`,
    DATABASE_MAPPINGS: `${API_BASE_URL}/debug/database-mappings`,
  },

  // Setup endpoints
  SETUP: {
    CRYPTO_MAPPINGS: `${API_BASE_URL}/setup/crypto-mappings`,
    STATUS: `${API_BASE_URL}/setup/status`,
  },
};

/**
 * Helper function to build query parameters
 */
export function buildQueryString(params: Record<string, any>): string {
  const queryParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach(item => queryParams.append(key, item.toString()));
      } else {
        queryParams.append(key, value.toString());
      }
    }
  });
  
  const queryString = queryParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Helper function to create authenticated fetch options
 */
export function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('aurum_access_token');
  return token ? { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  } : {
    'Content-Type': 'application/json'
  };
}