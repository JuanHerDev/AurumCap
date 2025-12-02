import { ApiInterceptor } from './api.interceptor';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface CryptoSearchResult {
  id: string;
  symbol: string;
  name: string;
  market_cap_rank?: number;
  thumb?: string;
  market_data?: any;
}

export interface CryptoInfo {
  id: string;
  symbol: string;
  name: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  price_change_percentage_24h: number;
  image: string;
  sparkline_in_7d?: { price: number[] };
}

export interface CryptoPriceData {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  market_cap: number;
  last_updated: string;
}

export interface CryptoProfile {
  id: string;
  symbol: string;
  name: string;
  description: { [key: string]: string };
  links: {
    homepage: string[];
    blockchain_site: string[];
    official_forum_url: string[];
    subreddit_url: string;
  };
  market_data: {
    current_price: { [key: string]: number };
    market_cap: { [key: string]: number };
    total_volume: { [key: string]: number };
    price_change_percentage_24h: number;
    price_change_percentage_7d: number;
    price_change_percentage_30d: number;
  };
  developer_data: any;
  community_data: any;
}

export interface TrendingCoin {
  coin_id: string;
  name: string;
  symbol: string;
  market_cap_rank: number;
  thumb: string;
  market_data: any;
}

export interface CryptoCategory {
  category_id: string;
  name: string;
  market_cap: number;
  volume_24h: number;
  top_3_coins: string[];
}

class CryptoService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * Universal search for ANY cryptocurrency
   */
  async universalSearch(query: string): Promise<CryptoSearchResult[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/v2/universal-search?query=${encodeURIComponent(query)}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error('Error in crypto universal search:', error);
      throw error;
    }
  }

  /**
   * Get info for ANY crypto using symbol, name or ID
   */
  async getCryptoInfo(identifier: string): Promise<CryptoInfo> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/v2/any/${encodeURIComponent(identifier)}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting crypto info:', error);
      throw error;
    }
  }

  /**
   * Get current price for a cryptocurrency (v1 endpoint)
   */
  async getCryptoPrice(symbol: string): Promise<CryptoPriceData> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/price/${symbol.toUpperCase()}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting crypto price:', error);
      throw error;
    }
  }

  /**
   * Get detailed profile for a cryptocurrency (v1 endpoint)
   */
  async getCryptoProfile(symbol: string, language: string = 'es'): Promise<CryptoProfile> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/profile/${symbol.toUpperCase()}?language=${language}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting crypto profile:', error);
      throw error;
    }
  }

  /**
   * Get market data for a cryptocurrency (v1 endpoint)
   */
  async getMarketData(symbol: string): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/market-data/${symbol.toUpperCase()}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting market data:', error);
      throw error;
    }
  }

  /**
   * Get historical data for a cryptocurrency (v1 endpoint)
   */
  async getHistoricalData(symbol: string, days: number = 30, interval: string = 'daily'): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/historical/${symbol.toUpperCase()}?days=${days}&interval=${interval}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting historical data:', error);
      throw error;
    }
  }

  /**
   * Get global crypto market data (v1 endpoint)
   */
  async getGlobalMarketData(): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/global/market`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting global market data:', error);
      throw error;
    }
  }

  /**
   * Search cryptocurrencies by name or symbol (v1 endpoint)
   */
  async searchCryptocurrencies(query: string): Promise<any[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/search?query=${encodeURIComponent(query)}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error('Error searching cryptocurrencies:', error);
      throw error;
    }
  }

  /**
   * Get trending cryptocurrencies (v1 endpoint)
   */
  async getTrendingCryptocurrencies(): Promise<any[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/trending`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.trending || [];
    } catch (error) {
      console.error('Error getting trending cryptocurrencies:', error);
      throw error;
    }
  }

  /**
   * Get trending crypto discovery (v2 endpoint)
   */
  async getTrendingDiscovery(): Promise<TrendingCoin[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/v2/discover/trending`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.trending || [];
    } catch (error) {
      console.error('Error getting trending discovery:', error);
      throw error;
    }
  }

  /**
   * Get crypto categories (v2 endpoint)
   */
  async getCryptoCategories(): Promise<CryptoCategory[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/v2/discover/categories`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.categories || [];
    } catch (error) {
      console.error('Error getting crypto categories:', error);
      throw error;
    }
  }

  /**
   * Get auto-updater status (v2 endpoint)
   */
  async getAutoUpdateStatus(): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/v2/auto-update/status`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting auto-update status:', error);
      throw error;
    }
  }

  /**
   * Force auto-update (v2 endpoint)
   */
  async forceAutoUpdate(): Promise<{ message: string }> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/crypto/v2/auto-update/force`,
        {
          method: 'POST',
        }
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error forcing auto-update:', error);
      throw error;
    }
  }

  /**
   * Get cached prices (v2 endpoint)
   */
  async getCachedPrices(symbol?: string): Promise<any> {
    try {
      const url = symbol 
        ? `${this.baseUrl}/crypto/v2/prices/cached?symbol=${symbol}`
        : `${this.baseUrl}/crypto/v2/prices/cached`;
      
      const response = await ApiInterceptor.fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting cached prices:', error);
      throw error;
    }
  }

  /**
   * Get sparkline data for crypto symbol
   */
  async getSparklineData(symbol: string, days: number = 7): Promise<number[]> {
    try {
      const historicalData = await this.getHistoricalData(symbol, days, 'daily');
      
      // Extract prices from historical data
      if (historicalData && historicalData.prices) {
        return historicalData.prices.map((p: any) => p[1]);
      }
      
      return [];
    } catch (error) {
      console.error('Error getting sparkline data:', error);
      return [];
    }
  }
}

export const cryptoService = new CryptoService();