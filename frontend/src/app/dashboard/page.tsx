"use client";

import { useState, useEffect } from "react";
import { portfolioService } from "@/services/portfolio.service";
import { cryptoService } from "@/services/crypto.service";
import { stockService } from "@/services/stocks.service";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";
import DashboardChart from "@/components/dashboard/DashboardChart"
import QuickActions from "@/components/dashboard/QuickActions";
import MarketOverview from "@/components/dashboard/MarketOverview";

export default function Dashboard() {
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [marketData, setMarketData] = useState<any>(null);
  const [trendingCrypto, setTrendingCrypto] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load portfolio data
      const portfolio = await portfolioService.getPortfolioSummary();
      setPortfolioData(portfolio);

      // Load market data in parallel
      const [cryptoTrending, marketStatus] = await Promise.all([
        cryptoService.getTrendingDiscovery(),
        stockService.getMarketStatus(),
      ]);

      setTrendingCrypto(cryptoTrending);
      setMarketData({
        marketStatus,
        trendingCrypto: cryptoTrending,
      });
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 text-sm">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  const userName = user?.full_name || user?.email?.split('@')[0] || "Investor";

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 pb-20">
      {/* Header */}
      <header className="bg-white px-4 py-4 border-b border-gray-200 sticky top-0 z-10">
        <div className="flex justify-between items-center max-w-6xl mx-auto">
          <h1 className="text-xl font-bold">
            Hello, <span className="text-[#B59F50]">{userName}</span>
          </h1>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className={`w-2 h-2 rounded-full ${
              marketData?.marketStatus?.is_market_open ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="hidden xs:inline">
              {marketData?.marketStatus?.is_market_open ? 'Market Open' : 'Market Closed'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Balance Card */}
        <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
          <div className="flex flex-col xs:flex-row justify-between items-start gap-3">
            <div className="flex-1">
              <p className="text-gray-500 text-xs mb-1">Total Balance</p>
              <h2 className="text-2xl sm:text-3xl font-bold mb-2">
                ${portfolioData?.summary?.total_value?.toLocaleString('en-US', { 
                  minimumFractionDigits: 2, 
                  maximumFractionDigits: 2 
                }) || '0.00'}
              </h2>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`${
                  (portfolioData?.summary?.total_roi || 0) >= 0 
                    ? 'text-green-500' 
                    : 'text-red-500'
                } font-semibold flex items-center gap-1 text-sm`}>
                  {portfolioData?.summary?.total_roi >= 0 ? '↗' : '↘'}
                  {Math.abs(portfolioData?.summary?.total_roi || 0).toFixed(2)}%
                </span>
                <span className="text-gray-500 text-xs">
                  Total ROI {(portfolioData?.summary?.total_roi || 0) >= 0 ? 'gain' : 'loss'}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-gray-500 text-xs">Assets</p>
              <p className="text-lg sm:text-xl font-bold text-[#B59F50]">
                {portfolioData?.summary?.asset_count || 0}
              </p>
            </div>
          </div>
        </section>

        {/* Performance Chart */}
        <DashboardChart 
          portfolioData={portfolioData}
          onRefresh={loadDashboardData}
        />

        {/* Market Overview */}
        {marketData && (
          <MarketOverview 
            marketStatus={marketData.marketStatus}
            trendingCrypto={trendingCrypto}
          />
        )}

        {/* Quick Actions */}
        <QuickActions />
      </div>
    </main>
  );
}