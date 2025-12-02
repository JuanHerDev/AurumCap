"use client";

import { useState, useEffect, useCallback } from 'react';
import { 
  portfolioService, 
  type InvestmentCard, 
  type PortfolioResponse,
  type AllocationData
} from '@/services/portfolio.service';
import { cryptoService } from '@/services/crypto.service';
import { stockService } from '@/services/stocks.service';

export interface PortfolioMetrics {
  totalInvested: number;
  totalCurrentValue: number;
  totalGain: number;
  totalROI: number;
}

export interface LiveInvestment extends InvestmentCard {
  sparkline_data?: number[];
  price_change_24h?: number;
  last_updated?: string;
}

export interface UsePortfolioResult {
  // Portfolio data
  investments: LiveInvestment[];
  summary: PortfolioResponse['summary'] | null;
  allocations: AllocationData | null;
  
  // Loading and error states
  loading: boolean;
  error: Error | null;
  
  // Actions
  refresh: () => Promise<void>;
  createInvestment: (data: any) => Promise<void>;
  updateInvestment: (id: number, data: any) => Promise<void>;
  deleteInvestment: (id: number) => Promise<void>;
  
  // Advanced features
  getAdvancedDashboard: () => Promise<any>;
  getRiskProfile: () => Promise<any>;
  createRiskProfile: (data: any) => Promise<any>;
  getDividendSummary: (year?: number) => Promise<any>;
  getInvestmentGoals: (activeOnly?: boolean) => Promise<any[]>;
  createInvestmentGoal: (data: any) => Promise<any>;
  
  // Market data
  getSparklineData: (symbol: string, assetType: string) => Promise<number[]>;
  
  // Metrics
  portfolioMetrics: PortfolioMetrics | null;
}

export function usePortfolio(): UsePortfolioResult {
  const [investments, setInvestments] = useState<LiveInvestment[]>([]);
  const [summary, setSummary] = useState<PortfolioResponse['summary'] | null>(null);
  const [allocations, setAllocations] = useState<AllocationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  /**
   * Load portfolio data from backend
   */
  const loadPortfolioData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Loading portfolio data...');
      
      // Load portfolio summary with investments
      const portfolioData = await portfolioService.getPortfolioSummary();
      setSummary(portfolioData.summary);
      
      // Enhance investments with live data
      const enhancedInvestments = await enhanceInvestmentsWithLiveData(portfolioData.investments);
      setInvestments(enhancedInvestments);
      
      // Load allocations
      const allocationData = await portfolioService.getAllocations();
      setAllocations(allocationData);
      
      console.log('✅ Portfolio data loaded successfully');
      setLastRefresh(new Date());
    } catch (err: any) {
      console.error('❌ Error loading portfolio data:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Enhance investments with live data (prices, sparklines, etc.)
   */
  const enhanceInvestmentsWithLiveData = async (investments: InvestmentCard[]): Promise<LiveInvestment[]> => {
    const enhanced: LiveInvestment[] = [];
    
    for (const investment of investments) {
      try {
        const enhancedInvestment: LiveInvestment = { ...investment };
        
        // Get sparkline data
        if (investment.asset_type === 'crypto') {
          try {
            const sparklineData = await cryptoService.getSparklineData(
              investment.symbol,
              7
            );
            enhancedInvestment.sparkline_data = sparklineData;
          } catch (sparklineError) {
            console.warn(`Could not load sparkline for ${investment.symbol}:`, sparklineError);
          }
          
          // Get 24h price change for crypto
          try {
            const cryptoInfo = await cryptoService.getCryptoInfo(investment.symbol);
            enhancedInvestment.price_change_24h = cryptoInfo.price_change_percentage_24h;
          } catch (priceError) {
            console.warn(`Could not load 24h change for ${investment.symbol}:`, priceError);
          }
        } else if (investment.asset_type === 'stock') {
          // Get sparkline data for stocks
          try {
            const historicalData = await stockService.getHistoricalData(
              investment.symbol,
              '1day',
              undefined,
              undefined
            );
            
            if (historicalData?.historical_data) {
              const prices = historicalData.historical_data.map(data => data.close);
              enhancedInvestment.sparkline_data = prices.slice(-30); // Last 30 days
            }
          } catch (sparklineError) {
            console.warn(`Could not load sparkline for stock ${investment.symbol}:`, sparklineError);
          }
        }
        
        enhanced.push(enhancedInvestment);
      } catch (error) {
        console.error(`Error enhancing investment ${investment.symbol}:`, error);
        enhanced.push({ ...investment }); // Add without enhancement
      }
    }
    
    return enhanced;
  };

  /**
   * Calculate portfolio metrics
   */
  const portfolioMetrics: PortfolioMetrics | null = summary ? {
    totalInvested: summary.total_invested,
    totalCurrentValue: summary.total_value,
    totalGain: summary.total_gain,
    totalROI: summary.total_roi,
  } : null;

  /**
   * Refresh portfolio data
   */
  const refresh = useCallback(async () => {
    await loadPortfolioData();
  }, [loadPortfolioData]);

  /**
   * Create new investment
   */
  const createInvestment = useCallback(async (data: any) => {
    setLoading(true);
    try {
      const result = await portfolioService.createInvestment(data);
      await loadPortfolioData(); // Refresh data
      return result;
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadPortfolioData]);

  /**
   * Update existing investment
   */
  const updateInvestment = useCallback(async (id: number, data: any) => {
    setLoading(true);
    try {
      const result = await portfolioService.updateInvestment(id, data);
      await loadPortfolioData(); // Refresh data
      return result;
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadPortfolioData]);

  /**
   * Delete investment
   */
  const deleteInvestment = useCallback(async (id: number) => {
    setLoading(true);
    try {
      await portfolioService.deleteInvestment(id);
      await loadPortfolioData(); // Refresh data
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadPortfolioData]);

  /**
   * Advanced portfolio features
   */
  const getAdvancedDashboard = useCallback(async () => {
    try {
      return await portfolioService.getAdvancedDashboard();
    } catch (err: any) {
      console.error('Error getting advanced dashboard:', err);
      throw err;
    }
  }, []);

  const getRiskProfile = useCallback(async () => {
    try {
      return await portfolioService.getRiskProfile();
    } catch (err: any) {
      console.error('Error getting risk profile:', err);
      throw err;
    }
  }, []);

  const createRiskProfile = useCallback(async (data: any) => {
    try {
      return await portfolioService.createRiskProfile(data);
    } catch (err: any) {
      console.error('Error creating risk profile:', err);
      throw err;
    }
  }, []);

  const getDividendSummary = useCallback(async (year?: number) => {
    try {
      return await portfolioService.getDividendSummary(year);
    } catch (err: any) {
      console.error('Error getting dividend summary:', err);
      throw err;
    }
  }, []);

  const getInvestmentGoals = useCallback(async (activeOnly: boolean = true) => {
    try {
      return await portfolioService.getInvestmentGoals(activeOnly);
    } catch (err: any) {
      console.error('Error getting investment goals:', err);
      throw err;
    }
  }, []);

  const createInvestmentGoal = useCallback(async (data: any) => {
    try {
      return await portfolioService.createInvestmentGoal(data);
    } catch (err: any) {
      console.error('Error creating investment goal:', err);
      throw err;
    }
  }, []);

  /**
   * Get sparkline data for symbol
   */
  const getSparklineData = useCallback(async (symbol: string, assetType: string) => {
    try {
      const result = await portfolioService.getSparklineData(symbol, assetType);
      return result.sparkline_data;
    } catch (err) {
      console.error('Error getting sparkline data:', err);
      return [];
    }
  }, []);

  /**
   * Load data on mount and auto-refresh
   */
  useEffect(() => {
    loadPortfolioData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadPortfolioData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [loadPortfolioData]);

  return {
    // Portfolio data
    investments,
    summary,
    allocations,
    
    // Loading and error states
    loading,
    error,
    
    // Actions
    refresh,
    createInvestment,
    updateInvestment,
    deleteInvestment,
    
    // Advanced features
    getAdvancedDashboard,
    getRiskProfile,
    createRiskProfile,
    getDividendSummary,
    getInvestmentGoals,
    createInvestmentGoal,
    
    // Market data
    getSparklineData,
    
    // Metrics
    portfolioMetrics,
  };
}