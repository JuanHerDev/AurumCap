import { ApiInterceptor } from './api.interceptor';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface FundamentalData {
  symbol: string;
  company_name: string;
  sector: string;
  industry: string;
  current_price: number;
  market_cap: number;
  pe_ratio: number;
  eps: number;
  dividend_yield: number;
  beta: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
  volume: number;
  avg_volume: number;
  data_quality: {
    completeness_percentage: number;
    filled_fields: number;
    total_fields: number;
    quality: string;
  };
  source: string;
  is_real_data: boolean;
  source_info?: string;
}

export interface HistoricalFundamental {
  period: string;
  revenue: number;
  net_income: number;
  eps: number;
  dividends_per_share: number;
  is_estimated: boolean;
  date: string;
}

export interface SectorMetrics {
  sector: string;
  average_pe_ratio: number;
  average_dividend_yield: number;
  average_roe: number;
  top_companies: Array<{
    symbol: string;
    name: string;
    market_cap: number;
    pe_ratio: number;
  }>;
  total_companies: number;
}

export interface EconomicEvent {
  event_id: string;
  country: string;
  event: string;
  previous: number;
  forecast: number;
  actual: number;
  importance: number;
  event_date: string;
  source: string;
}

export interface EarningsEvent {
  symbol: string;
  company_name: string;
  fiscal_period: string;
  eps_estimate: number;
  eps_actual: number;
  revenue_estimate: number;
  revenue_actual: number;
  report_date: string;
  source: string;
}

export interface UpcomingEvents {
  period_days: number;
  total_events: number;
  economic_events: number;
  earnings_events: number;
  events: Array<EconomicEvent | EarningsEvent>;
}

class FundamentalsService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * Get enhanced current fundamental data with REAL data sources
   */
  async getCurrentFundamentals(symbol: string): Promise<FundamentalData> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/fundamentals/current/${symbol}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting current fundamentals:', error);
      throw error;
    }
  }

  /**
   * Get historical fundamental data
   */
  async getHistoricalFundamentals(
    symbol: string,
    periodType: string = 'annual',
    limit: number = 10
  ): Promise<HistoricalFundamental[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/fundamentals/historical/${symbol}?period_type=${periodType}&limit=${limit}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.historical_data || [];
    } catch (error) {
      console.error('Error getting historical fundamentals:', error);
      throw error;
    }
  }

  /**
   * Get enhanced sector metrics
   */
  async getSectorMetrics(sector: string): Promise<SectorMetrics> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/fundamentals/sector/${encodeURIComponent(sector)}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting sector metrics:', error);
      throw error;
    }
  }

  /**
   * Get economic calendar events
   */
  async getEconomicCalendar(
    startDate: string,
    endDate: string,
    country: string = 'US'
  ): Promise<EconomicEvent[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/fundamentals/calendar/economic?start_date=${startDate}&end_date=${endDate}&country=${country}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.events || [];
    } catch (error) {
      console.error('Error getting economic calendar:', error);
      throw error;
    }
  }

  /**
   * Get earnings calendar events
   */
  async getEarningsCalendar(
    startDate: string,
    endDate: string,
    symbol?: string
  ): Promise<EarningsEvent[]> {
    try {
      let url = `${this.baseUrl}/fundamentals/calendar/earnings?start_date=${startDate}&end_date=${endDate}`;
      if (symbol) url += `&symbol=${symbol}`;
      
      const response = await ApiInterceptor.fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.earnings || [];
    } catch (error) {
      console.error('Error getting earnings calendar:', error);
      throw error;
    }
  }

  /**
   * Get upcoming economic and earnings events
   */
  async getUpcomingEvents(days: number = 7): Promise<UpcomingEvents> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/fundamentals/calendar/upcoming?days=${days}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting upcoming events:', error);
      throw error;
    }
  }

  /**
   * Get list of all available sectors
   */
  async getAllSectors(): Promise<string[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/fundamentals/sectors/all`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.data.sectors || [];
    } catch (error) {
      console.error('Error getting all sectors:', error);
      throw error;
    }
  }
}

export const fundamentalsService = new FundamentalsService();