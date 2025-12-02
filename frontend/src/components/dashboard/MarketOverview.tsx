"use client";

import { useState, useEffect } from 'react';
import { useMarketData } from '@/hooks/useMarketData';
import { cryptoService } from '@/services/crypto.service';
import { stockService } from '@/services/stocks.service';
import { 
  FaArrowUp, 
  FaArrowDown, 
  FaExternalLinkAlt, 
  FaSyncAlt,
  FaFire,
  FaChartLine,
  FaBuilding,
  FaBitcoin,
  FaRegClock
} from 'react-icons/fa';

interface MarketOverviewProps {
  marketStatus?: any;
  trendingCrypto?: any[];
}

interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface TrendingAsset {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  marketCapRank: number;
  type: 'crypto' | 'stock';
}

export default function MarketOverview({ marketStatus, trendingCrypto }: MarketOverviewProps) {
  const [indices, setIndices] = useState<MarketIndex[]>([
    { symbol: 'SPX', name: 'S&P 500', price: 4520.34, change: 15.67, changePercent: 0.35 },
    { symbol: 'DJI', name: 'Dow Jones', price: 35430.42, change: 89.23, changePercent: 0.25 },
    { symbol: 'NDX', name: 'NASDAQ', price: 15125.18, change: 45.67, changePercent: 0.30 },
    { symbol: 'BTC', name: 'Bitcoin', price: 42567.89, change: 856.32, changePercent: 2.05 },
  ]);
  
  const [trendingAssets, setTrendingAssets] = useState<TrendingAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'crypto' | 'stocks'>('crypto');
  
  const { getTrendingCrypto } = useMarketData();

  // Load market data
  const loadMarketData = async () => {
    setLoading(true);
    
    try {
      // Load trending crypto
      const trending = await getTrendingCrypto();
      const formattedCrypto = trending.slice(0, 5).map((crypto: any) => ({
        id: crypto.coin_id || crypto.id,
        symbol: crypto.symbol?.toUpperCase() || 'CRYPTO',
        name: crypto.name || 'Cryptocurrency',
        price: crypto.market_data?.current_price?.usd || 0,
        change24h: crypto.market_data?.price_change_percentage_24h || 0,
        marketCapRank: crypto.market_cap_rank || 999,
        type: 'crypto' as const,
      }));
      
      // Load major indices (simulated for now)
      const simulatedIndices: MarketIndex[] = [
        { symbol: 'SPX', name: 'S&P 500', price: 4520.34, change: 15.67, changePercent: 0.35 },
        { symbol: 'DJI', name: 'Dow Jones', price: 35430.42, change: 89.23, changePercent: 0.25 },
        { symbol: 'NDX', name: 'NASDAQ', price: 15125.18, change: 45.67, changePercent: 0.30 },
        { symbol: 'BTC', name: 'Bitcoin', price: 42567.89, change: 856.32, changePercent: 2.05 },
      ];
      
      setTrendingAssets(formattedCrypto);
      setIndices(simulatedIndices);
    } catch (error) {
      console.error('Error loading market data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1e9) {
      return `$${(value / 1e9).toFixed(2)}B`;
    }
    if (value >= 1e6) {
      return `$${(value / 1e6).toFixed(2)}M`;
    }
    if (value >= 1e3) {
      return `$${(value / 1e3).toFixed(2)}K`;
    }
    return `$${value.toFixed(2)}`;
  };

  // Format change with sign
  const formatChange = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  // Get market status color
  const getMarketStatusColor = () => {
    return marketStatus?.is_market_open ? 'text-green-500' : 'text-red-500';
  };

  // Get market status text
  const getMarketStatusText = () => {
    if (marketStatus?.is_market_open) {
      return 'Market Open';
    } else if (marketStatus?.next_opening) {
      return `Opens ${new Date(marketStatus.next_opening).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      return 'Market Closed';
    }
  };

  // Refresh data
  const handleRefresh = async () => {
    await loadMarketData();
  };

  // Initial load
  useEffect(() => {
    loadMarketData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMarketData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
        <div className="flex items-center gap-2">
          <FaChartLine className="text-[#B59F50]" size={20} />
          <h3 className="font-semibold text-base sm:text-lg">Market Overview</h3>
          
          {/* Market Status */}
          {marketStatus && (
            <div className="flex items-center gap-2 ml-2 px-2 py-1 bg-gray-100 rounded-full">
              <div className={`w-2 h-2 rounded-full ${getMarketStatusColor()}`}></div>
              <span className="text-xs font-medium text-gray-700">
                {getMarketStatusText()}
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('crypto')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'crypto'
                  ? "bg-[#B59F50] text-white"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Crypto
            </button>
            <button
              onClick={() => setActiveTab('stocks')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'stocks'
                  ? "bg-[#B59F50] text-white"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Stocks
            </button>
          </div>
          
          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-[#B59F50] transition-colors disabled:opacity-50"
          >
            <FaSyncAlt size={16} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500 text-sm">Loading market data...</p>
          </div>
        </div>
      ) : (
        <>
          {/* Major Indices */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <FaBuilding size={14} />
              Major Indices
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {indices.map((index) => (
                <div
                  key={index.symbol}
                  className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-semibold text-gray-900">{index.symbol}</div>
                      <div className="text-xs text-gray-500 truncate">{index.name}</div>
                    </div>
                    <div className={`flex items-center gap-1 text-sm font-medium ${
                      index.changePercent >= 0 ? 'text-green-500' : 'text-red-500'
                    }`}>
                      {index.changePercent >= 0 ? <FaArrowUp size={10} /> : <FaArrowDown size={10} />}
                      {formatChange(index.changePercent)}
                    </div>
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {formatCurrency(index.price)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trending Assets */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <FaFire size={14} className="text-orange-500" />
                {activeTab === 'crypto' ? 'Trending Cryptocurrencies' : 'Top Stocks'}
              </h4>
              <button className="text-xs text-[#B59F50] hover:text-[#A68F45] font-medium flex items-center gap-1">
                View All
                <FaExternalLinkAlt size={10} />
              </button>
            </div>

            {activeTab === 'crypto' ? (
              // Crypto Tab
              <div className="space-y-2">
                {trendingAssets.map((asset) => (
                  <div
                    key={asset.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-10 h-10 bg-linear-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                          <FaBitcoin size={16} />
                        </div>
                        {asset.marketCapRank <= 100 && (
                          <div className="absolute -top-1 -right-1 w-5 h-5 bg-[#B59F50] text-white text-xs rounded-full flex items-center justify-center">
                            {asset.marketCapRank}
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{asset.symbol}</div>
                        <div className="text-xs text-gray-500 truncate max-w-[120px]">
                          {asset.name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="font-bold text-gray-900">
                        {formatCurrency(asset.price)}
                      </div>
                      <div className={`text-sm font-medium ${
                        asset.change24h >= 0 ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {asset.change24h >= 0 ? '+' : ''}{asset.change24h.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Stocks Tab (Simulated for now)
              <div className="space-y-2">
                {[
                  { symbol: 'AAPL', name: 'Apple Inc.', price: 178.45, change: 1.23, changePercent: 0.69 },
                  { symbol: 'MSFT', name: 'Microsoft', price: 330.12, change: 2.45, changePercent: 0.75 },
                  { symbol: 'GOOGL', name: 'Alphabet', price: 132.56, change: 0.89, changePercent: 0.68 },
                  { symbol: 'AMZN', name: 'Amazon', price: 145.67, change: 1.34, changePercent: 0.93 },
                  { symbol: 'TSLA', name: 'Tesla', price: 245.78, change: 5.67, changePercent: 2.36 },
                ].map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-linear-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                        {stock.symbol.charAt(0)}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{stock.symbol}</div>
                        <div className="text-xs text-gray-500 truncate max-w-[120px]">
                          {stock.name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="font-bold text-gray-900">
                        ${stock.price.toFixed(2)}
                      </div>
                      <div className={`text-sm font-medium ${
                        stock.change >= 0 ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Market Stats */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <FaRegClock size={14} />
              Market Statistics
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-linear-to-br from-green-50 to-green-100 border border-green-200 rounded-xl">
                <div className="text-lg font-bold text-green-700">24h</div>
                <div className="text-xs text-green-600">Volume</div>
                <div className="text-sm font-semibold text-green-800 mt-1">$42.5B</div>
              </div>
              <div className="text-center p-3 bg-linear-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl">
                <div className="text-lg font-bold text-blue-700">52W High</div>
                <div className="text-xs text-blue-600">S&P 500</div>
                <div className="text-sm font-semibold text-blue-800 mt-1">4,607.07</div>
              </div>
              <div className="text-center p-3 bg-linear-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-xl">
                <div className="text-lg font-bold text-purple-700">Fear & Greed</div>
                <div className="text-xs text-purple-600">Index</div>
                <div className="text-sm font-semibold text-purple-800 mt-1">65 (Greed)</div>
              </div>
              <div className="text-center p-3 bg-linear-to-br from-amber-50 to-amber-100 border border-amber-200 rounded-xl">
                <div className="text-lg font-bold text-amber-700">VIX</div>
                <div className="text-xs text-amber-600">Volatility</div>
                <div className="text-sm font-semibold text-amber-800 mt-1">13.45</div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Market data is delayed by up to 15 minutes. Data shown is for informational purposes only.
            </p>
          </div>
        </>
      )}
    </section>
  );
}