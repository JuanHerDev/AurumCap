"use client";

import { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  ResponsiveContainer, 
  Tooltip, 
  Area,
  CartesianGrid
} from 'recharts';
import { FaSyncAlt, FaChartLine, FaArrowUp, FaArrowDown } from 'react-icons/fa';
import { usePortfolio } from '@/hooks/usePortfolio';
import { portfolioService } from '@/services/portfolio.service';

interface DashboardChartProps {
  portfolioData?: any;
  onRefresh?: () => void;
  initialPeriod?: '1M' | '3M' | '6M' | '1Y' | 'ALL';
}

interface ChartDataPoint {
  date: string;
  value: number;
  gain: number;
  roi: number;
}

export default function DashboardChart({ 
  portfolioData, 
  onRefresh, 
  initialPeriod = '1M' 
}: DashboardChartProps) {
  const [period, setPeriod] = useState<'1M' | '3M' | '6M' | '1Y' | 'ALL'>(initialPeriod);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { refresh: refreshPortfolio } = usePortfolio();

  // Fetch chart data based on selected period
  const fetchChartData = async () => {
    if (!portfolioData) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, you would fetch historical data from your API
      // For now, we'll generate sample data based on the portfolio
      const sampleData = generateSampleChartData(portfolioData, period);
      setChartData(sampleData);
    } catch (err: any) {
      console.error('Error fetching chart data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Generate sample chart data (replace with actual API call)
  const generateSampleChartData = (data: any, period: string): ChartDataPoint[] => {
    const baseValue = data?.summary?.total_value || 10000;
    const days = period === '1M' ? 30 : period === '3M' ? 90 : period === '6M' ? 180 : period === '1Y' ? 365 : 30;
    
    const dataPoints: ChartDataPoint[] = [];
    let currentValue = baseValue * 0.8; // Start 20% lower for visual effect
    
    // Generate data points with realistic fluctuations
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      // Add random fluctuation (±1-3% daily)
      const dailyChange = (Math.random() * 0.04 - 0.02) + 0.001; // -2% to +2% + slight positive bias
      currentValue *= (1 + dailyChange);
      
      // Add positive trend for longer periods
      if (period === '6M' || period === '1Y' || period === 'ALL') {
        currentValue *= 1.0003; // +0.03% daily trend
      }
      
      const invested = baseValue * 0.95; // Assume 95% of current value was invested
      const gain = currentValue - invested;
      const roi = (gain / invested) * 100;
      
      dataPoints.push({
        date: date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          ...(period === '1Y' || period === 'ALL' ? { year: '2-digit' } : {})
        }),
        value: Math.round(currentValue),
        gain: Math.round(gain),
        roi: parseFloat(roi.toFixed(2))
      });
    }
    
    return dataPoints;
  };

  // Calculate growth metrics
  const calculateGrowth = () => {
    if (chartData.length < 2) return { value: 0, isPositive: true, absolute: 0 };
    
    const current = chartData[chartData.length - 1]?.value || 0;
    const previous = chartData[chartData.length - 2]?.value || 0;
    
    if (previous === 0) return { value: 0, isPositive: true, absolute: 0 };
    
    const growthValue = ((current - previous) / previous) * 100;
    const absoluteGrowth = current - previous;
    
    return {
      value: Math.abs(growthValue).toFixed(2),
      isPositive: growthValue >= 0,
      absolute: absoluteGrowth
    };
  };

  // Handle refresh
  const handleRefresh = async () => {
    if (onRefresh) {
      onRefresh();
    }
    await refreshPortfolio();
    await fetchChartData();
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Initial data fetch
  useEffect(() => {
    fetchChartData();
  }, [period, portfolioData]);

  const growth = calculateGrowth();
  const currentValue = chartData[chartData.length - 1]?.value || 0;
  const totalGain = chartData[chartData.length - 1]?.gain || 0;
  const totalROI = chartData[chartData.length - 1]?.roi || 0;

  return (
    <section className="bg-white rounded-xl p-4 shadow-sm mb-4 border border-gray-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
        <div className="flex items-center gap-2">
          <FaChartLine className="text-[#B59F50]" size={20} />
          <h3 className="font-semibold text-base sm:text-lg">Portfolio Performance</h3>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Period Selector */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            {['1M', '3M', '6M', '1Y', 'ALL'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p as any)}
                className={`px-2 py-1 rounded-md text-xs font-medium transition-colors min-w-10 ${
                  period === p 
                    ? "bg-[#B59F50] text-white" 
                    : "text-gray-600 hover:text-gray-900"
                }`}
                disabled={loading}
              >
                {p}
              </button>
            ))}
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

      {/* Error State */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={fetchChartData}
            className="mt-2 text-sm text-red-600 hover:text-red-800"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="h-48 sm:h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500 text-sm">Loading chart data...</p>
          </div>
        </div>
      ) : (
        <>
          {/* Current Value and Growth */}
          <div className="mb-4">
            <div className="flex items-end gap-2 mb-1">
              <div className="text-2xl sm:text-3xl font-bold text-gray-900">
                {formatCurrency(currentValue)}
              </div>
              <div className={`flex items-center gap-1 text-sm font-medium ${
                growth.isPositive ? 'text-green-500' : 'text-red-500'
              }`}>
                {growth.isPositive ? <FaArrowUp size={12} /> : <FaArrowDown size={12} />}
                {growth.value}%
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div>
                <span className="font-medium">Total Gain:</span>{' '}
                <span className={totalGain >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {totalGain >= 0 ? '+' : ''}{formatCurrency(totalGain)}
                </span>
              </div>
              <div>
                <span className="font-medium">ROI:</span>{' '}
                <span className={totalROI >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {totalROI >= 0 ? '+' : ''}{totalROI.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="h-48 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#B59F50" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#B59F50" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 10 }}
                  padding={{ left: 5, right: 5 }}
                  interval="preserveStartEnd"
                  minTickGap={20}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 10 }}
                  width={40}
                  tickFormatter={(value) => {
                    if (value >= 1000000) return `$${(value/1000000).toFixed(1)}M`;
                    if (value >= 1000) return `$${(value/1000).toFixed(0)}k`;
                    return `$${value}`;
                  }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none',
                    borderRadius: '8px',
                    color: 'white',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    fontSize: '12px'
                  }}
                  formatter={(value: number, name: string) => {
                    if (name === 'value') return [formatCurrency(value), 'Value'];
                    if (name === 'gain') return [formatCurrency(value), 'Gain'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Area 
                  type="monotone" 
                  dataKey="value"
                  stroke="#B59F50"
                  fillOpacity={1}
                  fill="url(#colorValue)"
                  strokeWidth={0}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#B59F50" 
                  strokeWidth={2} 
                  dot={false}
                  activeDot={{ 
                    r: 4, 
                    fill: "#B59F50",
                    stroke: "#fff",
                    strokeWidth: 2
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Chart Legend */}
          <div className="flex justify-center mt-2">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <div className="w-3 h-0.5 bg-[#B59F50]"></div>
                <span>Portfolio Value</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-linear-to-b from-[#B59F50] to-transparent"></div>
                <span>Historical Trend</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Performance Metrics */}
      {!loading && !error && chartData.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Metrics</h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Current Value</div>
              <div className="font-bold text-gray-900">{formatCurrency(currentValue)}</div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Period Return</div>
              <div className={`font-bold ${growth.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {growth.isPositive ? '+' : ''}{growth.value}%
              </div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Total Gain</div>
              <div className={`font-bold ${totalGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalGain >= 0 ? '+' : ''}{formatCurrency(totalGain)}
              </div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Total ROI</div>
              <div className={`font-bold ${totalROI >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalROI >= 0 ? '+' : ''}{totalROI.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}