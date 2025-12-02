"use client";

import { useState, useEffect, useCallback } from 'react';
import { useMarketData } from '@/hooks/useMarketData';
import { cryptoService } from '@/services/crypto.service';
import { stockService } from '@/services/stocks.service';
import { FaSearch, FaCaretDown } from 'react-icons/fa';

interface AssetSearchProps {
  onSelect: (asset: any) => void;
  assetType?: 'crypto' | 'stock' | 'all';
  placeholder?: string;
}

export function AssetSearch({ onSelect, assetType = 'all', placeholder = "Search for assets..." }: AssetSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedAssetType, setSelectedAssetType] = useState<'crypto' | 'stock' | 'all'>(assetType);
  
  const { searchCrypto, searchStocks } = useMarketData();

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim().length < 2) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        let searchResults: any[] = [];

        if (selectedAssetType === 'crypto' || selectedAssetType === 'all') {
          const cryptoResults = await searchCrypto(query);
          searchResults = [...searchResults, ...cryptoResults.map(r => ({
            ...r,
            type: 'crypto',
            displayName: `${r.name} (${r.symbol.toUpperCase()})`,
          }))];
        }

        if (selectedAssetType === 'stock' || selectedAssetType === 'all') {
          const stockResults = await searchStocks(query);
          searchResults = [...searchResults, ...stockResults.map(r => ({
            ...r,
            type: 'stock',
            displayName: `${r.name} (${r.symbol})`,
          }))];
        }

        setResults(searchResults.slice(0, 10)); // Limit to 10 results
        setShowResults(true);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, selectedAssetType, searchCrypto, searchStocks]);

  const handleSelect = useCallback((asset: any) => {
    onSelect(asset);
    setQuery('');
    setShowResults(false);
    setResults([]);
  }, [onSelect]);

  return (
    <div className="relative w-full">
      <div className="flex gap-2 mb-2">
        <button
          onClick={() => setSelectedAssetType('all')}
          className={`px-3 py-1 text-sm rounded-lg ${
            selectedAssetType === 'all'
              ? 'bg-[#B59F50] text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setSelectedAssetType('crypto')}
          className={`px-3 py-1 text-sm rounded-lg ${
            selectedAssetType === 'crypto'
              ? 'bg-[#B59F50] text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Crypto
        </button>
        <button
          onClick={() => setSelectedAssetType('stock')}
          className={`px-3 py-1 text-sm rounded-lg ${
            selectedAssetType === 'stock'
              ? 'bg-[#B59F50] text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Stocks
        </button>
      </div>

      <div className="relative">
        <div className="flex items-center">
          <FaSearch className="absolute left-3 text-gray-400" size={16} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results.length > 0 && setShowResults(true)}
            placeholder={placeholder}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
          />
          {loading && (
            <div className="absolute right-3">
              <div className="w-4 h-4 border-2 border-[#B59F50] border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}
        </div>

        {showResults && results.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {results.map((asset, index) => (
              <button
                key={`${asset.type}-${asset.id || asset.symbol}-${index}`}
                onClick={() => handleSelect(asset)}
                className="w-full p-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 flex items-center gap-3"
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  asset.type === 'crypto' ? 'bg-purple-100' : 'bg-blue-100'
                }`}>
                  <span className={`font-semibold text-sm ${
                    asset.type === 'crypto' ? 'text-purple-600' : 'text-blue-600'
                  }`}>
                    {asset.symbol?.charAt(0) || 'A'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {asset.displayName || asset.name}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className={`px-2 py-0.5 rounded-full ${
                      asset.type === 'crypto' 
                        ? 'bg-purple-100 text-purple-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {asset.type}
                    </span>
                    {asset.market_cap_rank && (
                      <span>Rank #{asset.market_cap_rank}</span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {showResults && results.length === 0 && query.length >= 2 && !loading && (
        <div className="absolute z-10 w-full mt-1 p-4 bg-white border border-gray-200 rounded-lg shadow-lg text-center text-gray-500">
          No assets found
        </div>
      )}
    </div>
  );
}