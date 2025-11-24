import { useEffect, useState, useCallback } from "react";

interface Investment {
  id: number;
  asset: string;       // "BTC", "ETH", "AAPL", "TSLA"
  type: "crypto" | "stock";
  quantity: number; // 0.01 BTC, 5 ETH, 10 AAPL
  buy_price: number; // 120.000 BTC/USD
}

interface LivePriceMap {
  [symbol: string]: number; // { BTC: 97500, ETH: 3200, AAPL: 182.54 }
}

interface EnrichedInvestment extends Investment {
  current_price: number;
  current_value: number;
  gain: number;
  roi: number;
}

export function useLivePrices(
  investments: Investment[],
  pollIntervalMs: number = 10000
) {
  const [prices, setPrices] = useState<LivePriceMap>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * -----------------------------------------
   * 1️⃣ Fetch precios CRYPTO desde CoinGecko
   * -----------------------------------------
   */
  const fetchCryptoPrices = async (symbols: string[]): Promise<LivePriceMap> => {
    if (symbols.length === 0) return {};

    // CoinGecko espera ids → tú tienes símbolos → hacemos un mapeo
    const symbolToId: Record<string, string> = {
      BTC: "bitcoin",
      ETH: "ethereum",
      SOL: "solana",
      XRP: "ripple",
      // agregar otras cryptos que manejes...
    };

    const ids = symbols
      .map((s) => symbolToId[s.toUpperCase()])
      .filter(Boolean)
      .join(",");

    const url = `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd`;

    const res = await fetch(url);
    const data = await res.json();

    const result: LivePriceMap = {};
    for (const symbol of symbols) {
      const id = symbolToId[symbol.toUpperCase()];
      if (data[id]) {
        result[symbol] = data[id].usd;
      }
    }
    return result;
  };

  /**
   * -----------------------------------------
   * 2️⃣ Fetch precios STOCKS desde TwelveData
   * -----------------------------------------
   */
  const fetchStockPrices = async (symbols: string[]): Promise<LivePriceMap> => {
    if (symbols.length === 0) return {};

    const apiKey = process.env.NEXT_PUBLIC_TWELVEDATA_API_KEY;
    const result: LivePriceMap = {};

    for (const s of symbols) {
      const url = `https://api.twelvedata.com/price?symbol=${s}&apikey=${apiKey}`;
      const res = await fetch(url);
      const data = await res.json();

      if (data?.price) {
        result[s] = Number(data.price);
      }
    }

    return result;
  };

  /**
   * -----------------------------------------
   * 3️⃣ Fetch combinado (Crypto + Stocks)
   * -----------------------------------------
   */
  const fetchPrices = useCallback(async () => {
    if (!investments?.length) return;

    try {
      setLoading(true);
      setError(null);

      const cryptoSymbols = investments
        .filter((i) => i.type === "crypto")
        .map((i) => i.asset.toUpperCase());

      const stockSymbols = investments
        .filter((i) => i.type === "stock")
        .map((i) => i.asset.toUpperCase());

      const [crypto, stocks] = await Promise.all([
        fetchCryptoPrices(cryptoSymbols),
        fetchStockPrices(stockSymbols),
      ]);

      setPrices({ ...crypto, ...stocks });

    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [investments]);

  /**
   * -----------------------------------------
   * 4️⃣ Polling Automático
   * -----------------------------------------
   */
  useEffect(() => {
    fetchPrices();
    const interval = setInterval(fetchPrices, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchPrices, pollIntervalMs]);

  /**
   * -----------------------------------------
   * 5️⃣ Enriquecer inversiones con precios
   * -----------------------------------------
   */
  const enriched: EnrichedInvestment[] = investments.map((inv) => {
    const current_price = prices[inv.asset] ?? inv.buy_price;

    const current_value = current_price * inv.quantity;
    const initial_value = inv.buy_price * inv.quantity;
    const gain = current_value - initial_value;
    const roi = initial_value ? (gain / initial_value) * 100 : 0;

    return {
      ...inv,
      current_price,
      current_value,
      gain,
      roi,
    };
  });

  return {
    prices,
    investments: enriched,
    loading,
    error,
    refresh: fetchPrices,
  };
}
