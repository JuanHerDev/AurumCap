import { ApiInterceptor } from './api.interceptor';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface StockPrice {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  last_updated: string;
  exchange?: string;
}

export interface StockProfile {
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  sector?: string;
  industry?: string;
  market_cap: number;
  pe_ratio: number;
  dividend_yield: number;
  description: string;
  website: string;
  source: string;
}

export interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  previous_close: number;
  timestamp: string;
}

export interface StockHistoricalData {
  symbol: string;
  interval: string;
  data_points: number;
  historical_data: Array<{
    datetime: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

export interface StockFundamentalData {
  symbol: string;
  metrics: {
    pe_ratio: number;
    eps: number;
    roe: number;
    debt_to_equity: number;
    dividend_yield: number;
    market_cap: number;
  };
  earnings: Array<{
    date: string;
    actual: number;
    estimate: number;
  }>;
  dividends: Array<{
    ex_dividend_date: string;
    payment_date: string;
    amount: number;
  }>;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  currency: string;
  exchange: string;
  type: string;
}

export interface MarketStatus {
  is_market_open: boolean;
  opening_time?: string;
  closing_time?: string;
  next_opening?: string;
  indices: Array<{
    symbol: string;
    name: string;
    price: number;
    change: number;
    change_percent: number;
  }>;
}

export interface StockExchange {
  exchange_code: string;
  exchange_name: string;
  country: string;
  currency: string;
  opening_time?: string;
  closing_time?: string;
  timezone: string;
}

export interface StockSector {
  sector_id: string;
  sector_name: string;
  description: string;
  typical_pe_ratio: number;
  typical_dividend_yield: number;
  typical_roe: number;
  industries: Array<{
    industry_id: string;
    industry_name: string;
    description: string;
  }>;
}

class StockService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * Get current price for a stock
   */
  async getStockPrice(symbol: string, exchange?: string): Promise<StockPrice> {
    try {
      const url = exchange
        ? `${this.baseUrl}/stocks/price/${symbol}?exchange=${exchange}`
        : `${this.baseUrl}/stocks/price/${symbol}`;
      
      const response = await ApiInterceptor.fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting stock price:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive stock profile
   */
  async getStockProfile(symbol: string): Promise<StockProfile> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/profile/${symbol}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting stock profile:', error);
      throw error;
    }
  }

  /**
   * Get real-time stock quote
   */
  async getStockQuote(symbol: string): Promise<StockQuote> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/quote/${symbol}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting stock quote:', error);
      throw error;
    }
  }

  /**
   * Get historical stock data
   */
  async getHistoricalData(
    symbol: string,
    interval: string = '1day',
    startDate?: string,
    endDate?: string
  ): Promise<StockHistoricalData> {
    try {
      let url = `${this.baseUrl}/stocks/historical/${symbol}?interval=${interval}`;
      
      if (startDate) url += `&start_date=${startDate}`;
      if (endDate) url += `&end_date=${endDate}`;
      
      const response = await ApiInterceptor.fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting historical data:', error);
      throw error;
    }
  }

  /**
   * Get fundamental data for a stock
   */
  async getFundamentalData(symbol: string): Promise<StockFundamentalData> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/fundamentals/${symbol}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting fundamental data:', error);
      throw error;
    }
  }

  /**
   * Search for stocks by company name or symbol
   */
  async searchStocks(query: string): Promise<StockSearchResult[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/search?query=${encodeURIComponent(query)}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.results || [];
    } catch (error) {
      console.error('Error searching stocks:', error);
      throw error;
    }
  }

  /**
   * Get current market status and major indices
   */
  async getMarketStatus(): Promise<MarketStatus> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/market/status`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting market status:', error);
      throw error;
    }
  }

  /**
   * Get prices for multiple stocks efficiently
   */
  async getMultiplePrices(symbols: string[]): Promise<{[key: string]: StockPrice}> {
    try {
      const symbolsParam = symbols.join(',');
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/prices/batch?symbols=${symbolsParam}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.prices || {};
    } catch (error) {
      console.error('Error getting multiple prices:', error);
      throw error;
    }
  }

  /**
   * Get list of supported stock exchanges
   */
  async getSupportedExchanges(): Promise<StockExchange[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/exchanges`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.exchanges || [];
    } catch (error) {
      console.error('Error getting supported exchanges:', error);
      throw error;
    }
  }

  /**
   * Get list of stock sectors and industries
   */
  async getStockSectors(): Promise<StockSector[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/sectors`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.sectors || [];
    } catch (error) {
      console.error('Error getting stock sectors:', error);
      throw error;
    }
  }

  /**
   * Force refresh cache for a stock
   */
  async refreshStockCache(symbol: string): Promise<{ message: string }> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/stocks/cache/refresh/${symbol}`,
        {
          method: 'POST',
        }
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error refreshing stock cache:', error);
      throw error;
    }
  }
}

export const stockService = new StockService();