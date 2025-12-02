"use client";

import { useState, useCallback } from 'react';
import { cryptoService, type CryptoSearchResult, type CryptoInfo } from '@/services/crypto.service';
import { stockService, type StockSearchResult, type StockPrice } from '@/services/stocks.service';
import { fundamentalsService, type FundamentalData } from '@/services/fundamentals.service';

export interface UseMarketDataResult {
  // Search functions
  searchCrypto: (query: string) => Promise<CryptoSearchResult[]>;
  searchStocks: (query: string) => Promise<StockSearchResult[]>;
  
  // Crypto functions
  getCryptoInfo: (identifier: string) => Promise<CryptoInfo>;
  getCryptoPrice: (symbol: string) => Promise<any>;
  getCryptoProfile: (symbol: string, language?: string) => Promise<any>;
  getTrendingCrypto: () => Promise<any[]>;
  getCryptoCategories: () => Promise<any[]>;
  
  // Stock functions
  getStockPrice: (symbol: string, exchange?: string) => Promise<StockPrice>;
  getStockProfile: (symbol: string) => Promise<any>;
  getStockQuote: (symbol: string) => Promise<any>;
  getHistoricalData: (
    symbol: string, 
    interval?: string, 
    startDate?: string, 
    endDate?: string
  ) => Promise<any>;
  getMultiplePrices: (symbols: string[]) => Promise<any>;
  
  // Fundamentals functions
  getFundamentals: (symbol: string) => Promise<FundamentalData>;
  getHistoricalFundamentals: (
    symbol: string, 
    periodType?: string, 
    limit?: number
  ) => Promise<any[]>;
  getSectorMetrics: (sector: string) => Promise<any>;
  getEconomicCalendar: (
    startDate: string, 
    endDate: string, 
    country?: string
  ) => Promise<any[]>;
  getEarningsCalendar: (
    startDate: string, 
    endDate: string, 
    symbol?: string
  ) => Promise<any[]>;
  getUpcomingEvents: (days?: number) => Promise<any>;
  
  // Loading and error states
  loading: boolean;
  error: Error | null;
}

export function useMarketData(): UseMarketDataResult {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Universal crypto search
   */
  const searchCrypto = useCallback(async (query: string): Promise<CryptoSearchResult[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await cryptoService.universalSearch(query);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Stock search
   */
  const searchStocks = useCallback(async (query: string): Promise<StockSearchResult[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await stockService.searchStocks(query);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get crypto info by symbol, name or ID
   */
  const getCryptoInfo = useCallback(async (identifier: string): Promise<CryptoInfo> => {
    setLoading(true);
    setError(null);
    
    try {
      return await cryptoService.getCryptoInfo(identifier);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get crypto price (v1 endpoint)
   */
  const getCryptoPrice = useCallback(async (symbol: string): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await cryptoService.getCryptoPrice(symbol);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get crypto profile (v1 endpoint)
   */
  const getCryptoProfile = useCallback(async (symbol: string, language: string = 'es'): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await cryptoService.getCryptoProfile(symbol, language);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get trending cryptocurrencies
   */
  const getTrendingCrypto = useCallback(async (): Promise<any[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await cryptoService.getTrendingDiscovery();
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get crypto categories
   */
  const getCryptoCategories = useCallback(async (): Promise<any[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await cryptoService.getCryptoCategories();
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get stock price
   */
  const getStockPrice = useCallback(async (symbol: string, exchange?: string): Promise<StockPrice> => {
    setLoading(true);
    setError(null);
    
    try {
      return await stockService.getStockPrice(symbol, exchange);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get stock profile
   */
  const getStockProfile = useCallback(async (symbol: string): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await stockService.getStockProfile(symbol);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get stock quote
   */
  const getStockQuote = useCallback(async (symbol: string): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await stockService.getStockQuote(symbol);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get historical data
   */
  const getHistoricalData = useCallback(async (
    symbol: string,
    interval: string = '1day',
    startDate?: string,
    endDate?: string
  ): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await stockService.getHistoricalData(symbol, interval, startDate, endDate);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get multiple prices
   */
  const getMultiplePrices = useCallback(async (symbols: string[]): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await stockService.getMultiplePrices(symbols);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get fundamentals data
   */
  const getFundamentals = useCallback(async (symbol: string): Promise<FundamentalData> => {
    setLoading(true);
    setError(null);
    
    try {
      return await fundamentalsService.getCurrentFundamentals(symbol);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get historical fundamentals
   */
  const getHistoricalFundamentals = useCallback(async (
    symbol: string,
    periodType: string = 'annual',
    limit: number = 10
  ): Promise<any[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await fundamentalsService.getHistoricalFundamentals(symbol, periodType, limit);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get sector metrics
   */
  const getSectorMetrics = useCallback(async (sector: string): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await fundamentalsService.getSectorMetrics(sector);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get economic calendar
   */
  const getEconomicCalendar = useCallback(async (
    startDate: string,
    endDate: string,
    country: string = 'US'
  ): Promise<any[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await fundamentalsService.getEconomicCalendar(startDate, endDate, country);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get earnings calendar
   */
  const getEarningsCalendar = useCallback(async (
    startDate: string,
    endDate: string,
    symbol?: string
  ): Promise<any[]> => {
    setLoading(true);
    setError(null);
    
    try {
      return await fundamentalsService.getEarningsCalendar(startDate, endDate, symbol);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get upcoming events
   */
  const getUpcomingEvents = useCallback(async (days: number = 7): Promise<any> => {
    setLoading(true);
    setError(null);
    
    try {
      return await fundamentalsService.getUpcomingEvents(days);
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // Search functions
    searchCrypto,
    searchStocks,
    
    // Crypto functions
    getCryptoInfo,
    getCryptoPrice,
    getCryptoProfile,
    getTrendingCrypto,
    getCryptoCategories,
    
    // Stock functions
    getStockPrice,
    getStockProfile,
    getStockQuote,
    getHistoricalData,
    getMultiplePrices,
    
    // Fundamentals functions
    getFundamentals,
    getHistoricalFundamentals,
    getSectorMetrics,
    getEconomicCalendar,
    getEarningsCalendar,
    getUpcomingEvents,
    
    // Loading and error states
    loading,
    error,
  };
}