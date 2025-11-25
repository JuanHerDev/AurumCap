// services/portfolioService.ts
export interface PortfolioHistory {
  date: string;
  total_value: number;
  return_percentage: number;
}

export interface PortfolioSummary {
  total_balance: number;
  total_invested: number;
  total_profit: number;
  monthly_growth: number;
  annual_return: number;
  asset_count: number;
}

class PortfolioService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  }

  async getPortfolioHistory(period: string = '6M'): Promise<PortfolioHistory[]> {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${this.baseUrl}/portfolio/history?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching portfolio history:', error);
      throw error;
    }
  }

  async getPortfolioSummary(): Promise<PortfolioSummary> {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${this.baseUrl}/portfolio/summary`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching portfolio summary:', error);
      throw error;
    }
  }

  // Para usar cuando implementes el endpoint real en FastAPI
  async getRealTimePortfolioValue(): Promise<number> {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${this.baseUrl}/portfolio/current-value`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      return data.current_value;
    } catch (error) {
      console.error('Error fetching real-time portfolio value:', error);
      throw error;
    }
  }
}

export const portfolioService = new PortfolioService();