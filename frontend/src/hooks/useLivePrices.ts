import { useEffect, useState, useCallback } from "react";

interface Investment {
  id: number;
  symbol: string;
  asset?: string;
  type?: "crypto" | "stock";
  asset_type?: "crypto" | "stock";
  quantity: number;
  buy_price?: number;
  purchase_price?: number;
  invested_amount: number;
}

interface LivePriceMap {
  [symbol: string]: number;
}

interface EnrichedInvestment extends Investment {
  current_price: number;
  current_value: number;
  gain: number;
  roi: number;
}

interface PortfolioMetrics {
  totalInvested: number;
  totalCurrentValue: number;
  totalGain: number;
  totalROI: number;
}

// Convert a value to number safely
const safeToNumber = (value: any, defaultValue: number = 0): number => {
  if (value === null || value === undefined) return defaultValue;
  
  const num = Number(value);
  return isNaN(num) ? defaultValue : num;
};

// Format number to fixed decimals
const formatNumber = (value: number, decimals: number = 2): number => {
  return Number(parseFloat(value.toString()).toFixed(decimals));
};

export function useLivePrices(
  investments: Investment[],
  pollIntervalMs: number = 30000
) {
  const [prices, setPrices] = useState<LivePriceMap>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Fetch ALL prices through backend (crypto + stocks)
   */
  const fetchPrices = useCallback(async () => {
    if (!investments?.length) {
      setPrices({});
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Get unique symbols from investments
      const allSymbols = [...new Set(investments.map(i => i.symbol.toUpperCase()))];
      
      if (allSymbols.length === 0) {
        setPrices({});
        return;
      }

      console.log("🔍 [useLivePrices] Fetching prices for symbols:", allSymbols);

      // Use backend endpoint to get all prices
      const symbolsParam = allSymbols.join(',');
      const response = await fetch(`http://127.0.0.1:8000/prices/all?symbols=${symbolsParam}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });

      if (!response.ok) {
        throw new Error(`Backend returned status: ${response.status}`);
      }
      
      const priceData = await response.json();
      
      console.log("[useLivePrices] Prices received from backend:", priceData);

      // Convert strings to numbers safely
      const numericPrices: LivePriceMap = {};
      Object.keys(priceData).forEach(symbol => {
        if (priceData[symbol] !== null && priceData[symbol] !== undefined) {
          numericPrices[symbol] = safeToNumber(priceData[symbol]);
        }
      });

      setPrices(numericPrices);

    } catch (err: any) {
      console.error('[useLivePrices] Error fetching prices:', err);
      setError(err);
      
      // Fallback: use purchase prices if available
      const fallbackPrices: LivePriceMap = {};
      investments.forEach(inv => {
        const fallbackPrice = inv.purchase_price || 
                            (inv.invested_amount && inv.quantity ? 
                             inv.invested_amount / inv.quantity : 0);
        fallbackPrices[inv.symbol] = safeToNumber(fallbackPrice);
      });
      setPrices(fallbackPrices);
    } finally {
      setLoading(false);
    }
  }, [investments]);

  /**
   * Automatic Polling
   */
  useEffect(() => {
    fetchPrices();
    
    const interval = setInterval(fetchPrices, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchPrices, pollIntervalMs]);

  /**
   * Enrich investments with live prices and calculated metrics
   */
  const enriched: EnrichedInvestment[] = investments.map((inv) => {
    // Get current price with fallbacks
    const rawCurrentPrice = prices[inv.symbol] ?? 
                           inv.purchase_price ?? 
                           (inv.invested_amount && inv.quantity ? 
                            inv.invested_amount / inv.quantity : 0);
    
    // Convert to number safely
    const current_price = safeToNumber(rawCurrentPrice);
    const quantity = safeToNumber(inv.quantity);
    const invested_amount = safeToNumber(inv.invested_amount);
    
    // Calculate metrics
    const current_value = current_price * quantity;
    const gain = current_value - invested_amount;
    const roi = invested_amount > 0 ? (gain / invested_amount) * 100 : 0;

    return {
      ...inv,
      current_price: formatNumber(current_price),
      current_value: formatNumber(current_value), 
      gain: formatNumber(gain),
      roi: formatNumber(roi),
    };
  });

  /**
   * Metrics for the entire portfolio
   */
  const totalInvested = safeToNumber(enriched.reduce((sum, inv) => sum + safeToNumber(inv.invested_amount), 0));
  const totalCurrentValue = safeToNumber(enriched.reduce((sum, inv) => sum + safeToNumber(inv.current_value), 0));
  const totalGain = totalCurrentValue - totalInvested;
  const totalROI = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0;

  const portfolioMetrics: PortfolioMetrics = {
    totalInvested: formatNumber(totalInvested),
    totalCurrentValue: formatNumber(totalCurrentValue),
    totalGain: formatNumber(totalGain),
    totalROI: formatNumber(totalROI)
  };

  return {
    prices,
    investments: enriched,
    loading,
    error,
    refresh: fetchPrices,
    portfolioMetrics
  };
}