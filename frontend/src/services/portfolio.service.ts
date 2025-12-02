import { ApiInterceptor } from './api.interceptor';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface PortfolioMetrics {
  total_balance: number;
  total_invested: number;
  total_profit: number;
  monthly_growth: number;
  annual_return: number;
  asset_count: number;
}

export interface InvestmentCard {
  id: number;
  symbol: string;
  asset_name: string;
  asset_type: string;
  current_price: number;
  current_value: number;
  quantity: number;
  invested_amount: number;
  gain: number;
  roi: number;
  platform_name?: string;
  sparkline_data?: number[];
}

export interface InvestmentDetail extends InvestmentCard {
  purchase_price: number;
  purchase_date: string;
  currency: string;
  notes?: string;
  performance_history?: Array<{
    date: string;
    price: number;
    value: number;
  }>;
}

export interface AllocationData {
  by_asset_type: Array<{
    type: string;
    value: number;
    percentage: number;
    count: number;
  }>;
  by_platform: Array<{
    platform: string;
    value: number;
    percentage: number;
    count: number;
  }>;
  by_sector?: Array<{
    sector: string;
    value: number;
    percentage: number;
  }>;
}

export interface PortfolioResponse {
  investments: InvestmentCard[];
  summary: {
    total_value: number;
    total_invested: number;
    total_gain: number;
    total_roi: number;
    asset_count: number;
  };
}

export interface PortfolioAdvancedDashboard {
  health_score: number;
  rebalancing: any;
  dividends: any;
  goal_alerts: any[];
  goals_summary: Array<{
    id: number;
    name: string;
    progress: number;
    target_date: string;
    months_remaining: number;
  }>;
  active_alerts: number;
  dashboard_updated: string;
}

class PortfolioService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * Get portfolio summary with investments for dashboard
   */
  async getPortfolioSummary(): Promise<PortfolioResponse> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/investments`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching portfolio summary:', error);
      throw error;
    }
  }

  /**
   * Get data for investment cards (optimized for UI cards)
   */
  async getInvestmentCards(): Promise<InvestmentCard[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/investment-cards`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching investment cards:', error);
      throw error;
    }
  }

  /**
   * Get detailed data for investment modal
   */
  async getInvestmentDetail(investmentId: number): Promise<InvestmentDetail> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/investment-detail/${investmentId}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching investment detail:', error);
      throw error;
    }
  }

  /**
   * Create new investment
   */
  async createInvestment(investmentData: any): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/investments`,
        {
          method: 'POST',
          body: JSON.stringify(investmentData),
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating investment:', error);
      throw error;
    }
  }

  /**
   * Update existing investment
   */
  async updateInvestment(investmentId: number, investmentData: any): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/investments/${investmentId}`,
        {
          method: 'PUT',
          body: JSON.stringify(investmentData),
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating investment:', error);
      throw error;
    }
  }

  /**
   * Delete investment
   */
  async deleteInvestment(investmentId: number): Promise<void> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/investments/${investmentId}`,
        {
          method: 'DELETE',
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting investment:', error);
      throw error;
    }
  }

  /**
   * Get portfolio allocations
   */
  async getAllocations(): Promise<AllocationData> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/analytics/allocations`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching allocations:', error);
      throw error;
    }
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/analytics/performance`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
      throw error;
    }
  }

  /**
   * Get sparkline data for a symbol
   */
  async getSparklineData(symbol: string, assetType: string): Promise<{sparkline_data: number[]}> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/sparkline/${symbol}?asset_type=${assetType}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching sparkline data:', error);
      // Return empty sparkline as fallback
      return { sparkline_data: [] };
    }
  }

  /**
   * Get advanced portfolio dashboard data
   */
  async getAdvancedDashboard(): Promise<PortfolioAdvancedDashboard> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/advanced/dashboard`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching advanced dashboard:', error);
      throw error;
    }
  }

  /**
   * Get risk profile
   */
  async getRiskProfile(): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/advanced/risk-profile`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching risk profile:', error);
      throw error;
    }
  }

  /**
   * Create or update risk profile
   */
  async createRiskProfile(profileData: any): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/advanced/risk-profile`,
        {
          method: 'POST',
          body: JSON.stringify(profileData),
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating risk profile:', error);
      throw error;
    }
  }

  /**
   * Get current allocation
   */
  async getCurrentAllocation(): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/advanced/allocation/current`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching current allocation:', error);
      throw error;
    }
  }

  /**
   * Get dividend summary
   */
  async getDividendSummary(year?: number): Promise<any> {
    try {
      const url = year 
        ? `${this.baseUrl}/portfolio/advanced/dividends/summary?year=${year}`
        : `${this.baseUrl}/portfolio/advanced/dividends/summary`;
      
      const response = await ApiInterceptor.fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching dividend summary:', error);
      throw error;
    }
  }

  /**
   * Get investment goals
   */
  async getInvestmentGoals(activeOnly: boolean = true): Promise<any[]> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/advanced/goals?active_only=${activeOnly}`
      );
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching investment goals:', error);
      throw error;
    }
  }

  /**
   * Create investment goal
   */
  async createInvestmentGoal(goalData: any): Promise<any> {
    try {
      const response = await ApiInterceptor.fetchWithAuth(
        `${this.baseUrl}/portfolio/advanced/goals`,
        {
          method: 'POST',
          body: JSON.stringify(goalData),
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating investment goal:', error);
      throw error;
    }
  }
}

export const portfolioService = new PortfolioService();