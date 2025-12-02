"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  FaPlus, 
  FaChartLine, 
  FaCalculator, 
  FaBookOpen, 
  FaBell, 
  FaCog,
  FaExchangeAlt,
  FaDownload,
  FaFilter
} from 'react-icons/fa';
import { AssetSearch } from '@/components/AssetSearch';

interface QuickAction {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  href?: string;
  onClick?: () => void;
  color: string;
  badge?: string;
}

export default function QuickActions() {
  const router = useRouter();
  const [showAssetSearch, setShowAssetSearch] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);

  // Define quick actions
  const quickActions: QuickAction[] = [
    {
      id: 'add-investment',
      icon: <FaPlus size={20} />,
      title: 'Add Investment',
      description: 'Add new asset to portfolio',
      onClick: () => setShowAssetSearch(true),
      color: 'bg-green-500',
    },
    {
      id: 'portfolio',
      icon: <FaChartLine size={20} />,
      title: 'Portfolio',
      description: 'View all investments',
      href: '/portfolio',
      color: 'bg-blue-500',
    },
    {
      id: 'simulator',
      icon: <FaCalculator size={20} />,
      title: 'Simulator',
      description: 'Test investment strategies',
      href: '/simulator',
      color: 'bg-purple-500',
    },
    {
      id: 'learn',
      icon: <FaBookOpen size={20} />,
      title: 'Learn',
      description: 'Educational resources',
      href: '/learn',
      color: 'bg-amber-500',
      badge: 'New',
    },
    {
      id: 'alerts',
      icon: <FaBell size={20} />,
      title: 'Alerts',
      description: 'Price & portfolio alerts',
      href: '/alerts',
      color: 'bg-red-500',
    },
    {
      id: 'settings',
      icon: <FaCog size={20} />,
      title: 'Settings',
      description: 'Account configuration',
      href: '/settings',
      color: 'bg-gray-500',
    },
    {
      id: 'rebalance',
      icon: <FaExchangeAlt size={20} />,
      title: 'Rebalance',
      description: 'Optimize portfolio',
      href: '/portfolio?tab=rebalance',
      color: 'bg-teal-500',
    },
    {
      id: 'reports',
      icon: <FaDownload size={20} />,
      title: 'Reports',
      description: 'Export portfolio data',
      onClick: () => alert('Export feature coming soon!'),
      color: 'bg-indigo-500',
    },
  ];

  // Handle asset selection
  const handleAssetSelect = (asset: any) => {
    setSelectedAsset(asset);
    setShowAssetSearch(false);
    
    // Navigate to add investment with pre-filled data
    router.push(`/portfolio/new?symbol=${asset.symbol}&type=${asset.type}&name=${encodeURIComponent(asset.name)}`);
  };

  // Handle action click
  const handleActionClick = (action: QuickAction) => {
    if (action.onClick) {
      action.onClick();
    } else if (action.href) {
      router.push(action.href);
    }
  };

  // Get recently added investments (simulated)
  const recentInvestments = [
    { symbol: 'BTC', name: 'Bitcoin', type: 'crypto', change: '+5.2%' },
    { symbol: 'AAPL', name: 'Apple Inc.', type: 'stock', change: '+2.1%' },
    { symbol: 'ETH', name: 'Ethereum', type: 'crypto', change: '+8.7%' },
  ];

  return (
    <>
      {/* Asset Search Modal */}
      {showAssetSearch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Add Investment</h3>
              <button
                onClick={() => setShowAssetSearch(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Search for cryptocurrencies, stocks, or other assets to add to your portfolio
            </p>
            <AssetSearch onSelect={handleAssetSelect} />
          </div>
        </div>
      )}

      {/* Quick Actions Section */}
      <section className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          <div className="flex items-center gap-2">
            <button className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
              <FaFilter size={10} />
              <span>Customize</span>
            </button>
          </div>
        </div>

        {/* Actions Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {quickActions.map((action) => (
            <button
              key={action.id}
              onClick={() => handleActionClick(action)}
              className="group relative bg-white rounded-xl p-4 shadow-sm border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all duration-200 text-left"
            >
              {/* Badge */}
              {action.badge && (
                <span className="absolute -top-2 -right-2 px-2 py-1 bg-[#B59F50] text-white text-xs font-semibold rounded-full">
                  {action.badge}
                </span>
              )}
              
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className={`w-12 h-12 ${action.color} rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform duration-200`}>
                  {action.icon}
                </div>
                
                {/* Text Content */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-gray-900 text-sm mb-1 truncate">
                    {action.title}
                  </h4>
                  <p className="text-xs text-gray-500 line-clamp-2">
                    {action.description}
                  </p>
                </div>
              </div>
              
              {/* Hover Effect */}
              <div className="absolute inset-0 rounded-xl border-2 border-transparent group-hover:border-[#B59F50] transition-colors duration-200 pointer-events-none"></div>
            </button>
          ))}
        </div>
      </section>

      {/* Recent Activity */}
      <section className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h4 className="font-semibold text-gray-900 mb-3">Recent Activity</h4>
        
        <div className="space-y-3">
          {recentInvestments.map((investment) => (
            <div 
              key={investment.symbol}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group cursor-pointer"
              onClick={() => router.push(`/portfolio?symbol=${investment.symbol}`)}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  investment.type === 'crypto' ? 'bg-purple-100' : 'bg-blue-100'
                }`}>
                  <span className={`font-bold ${
                    investment.type === 'crypto' ? 'text-purple-600' : 'text-blue-600'
                  }`}>
                    {investment.symbol.charAt(0)}
                  </span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">
                    {investment.symbol}
                  </div>
                  <div className="text-xs text-gray-500">
                    {investment.name}
                  </div>
                </div>
              </div>
              
              <div className={`text-sm font-semibold ${
                investment.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
              }`}>
                {investment.change}
              </div>
            </div>
          ))}
        </div>

        {/* View All Link */}
        <div className="mt-4 pt-3 border-t border-gray-200">
          <button
            onClick={() => router.push('/portfolio')}
            className="w-full text-center text-sm text-[#B59F50] hover:text-[#A68F45] font-medium"
          >
            View Full Portfolio →
          </button>
        </div>
      </section>

      {/* Stats Summary */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="text-center p-3 bg-linear-to-br from-green-50 to-green-100 border border-green-200 rounded-xl">
          <div className="text-2xl font-bold text-green-700">8</div>
          <div className="text-xs text-green-600">Active Assets</div>
        </div>
        <div className="text-center p-3 bg-linear-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl">
          <div className="text-2xl font-bold text-blue-700">+12.5%</div>
          <div className="text-xs text-blue-600">Avg. ROI</div>
        </div>
        <div className="text-center p-3 bg-linear-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-xl">
          <div className="text-2xl font-bold text-purple-700">3</div>
          <div className="text-xs text-purple-600">Platforms</div>
        </div>
      </div>
    </>
  );
}