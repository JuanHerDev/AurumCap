import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search as SearchIcon, X, TrendingUp, Bitcoin, BarChart2 } from 'lucide-react'
import client from '../api/client'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Skeleton from '../components/ui/Skeleton'

// Asset type icon
const AssetIcon = ({ type, symbol }) => {
  const colors = {
    crypto: { bg: 'rgba(245,200,66,0.12)', color: 'var(--gold)' },
    stock:  { bg: 'rgba(129,140,248,0.12)', color: '#818CF8' },
    etf:    { bg: 'rgba(0,200,150,0.12)', color: 'var(--green)' },
  }
  const { bg, color } = colors[type] || colors.stock

  return (
    <div
      className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0"
      style={{ background: bg, color }}
    >
      {symbol.slice(0, 2)}
    </div>
  )
}

// Asset type badge
const TypeBadge = ({ type }) => {
  const config = {
    crypto: { label: 'Crypto', color: 'var(--gold)',  bg: 'rgba(245,200,66,0.1)'  },
    stock:  { label: 'Stock',  color: '#818CF8',       bg: 'rgba(129,140,248,0.1)' },
    etf:    { label: 'ETF',    color: 'var(--green)',  bg: 'rgba(0,200,150,0.1)'   },
  }
  const { label, color, bg } = config[type] || config.stock

  return (
    <span
      className="px-2 py-0.5 rounded-md text-xs font-medium"
      style={{ background: bg, color }}
    >
      {label}
    </span>
  )
}

// Popular assets to show before searching
const POPULAR = [
  { symbol: 'AAPL',  name: 'Apple Inc.',         asset_type: 'stock'  },
  { symbol: 'TSLA',  name: 'Tesla, Inc.',         asset_type: 'stock'  },
  { symbol: 'MSFT',  name: 'Microsoft Corp.',     asset_type: 'stock'  },
  { symbol: 'BTC',   name: 'Bitcoin',             asset_type: 'crypto' },
  { symbol: 'ETH',   name: 'Ethereum',            asset_type: 'crypto' },
  { symbol: 'SPY',   name: 'SPDR S&P 500 ETF',   asset_type: 'etf'    },
  { symbol: 'QQQ',   name: 'Invesco QQQ Trust',   asset_type: 'etf'    },
  { symbol: 'GOOGL', name: 'Alphabet Inc.',        asset_type: 'stock'  },
]

export default function Search() {
  const navigate = useNavigate()
  const inputRef = useRef(null)

  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  // Debounce search — wait 400ms after user stops typing
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setSearched(false)
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      setSearched(true)
      try {
        const { data } = await client.get(`/search?q=${encodeURIComponent(query)}&limit=15`)
        setResults(data.results || [])
      } catch (err) {
        console.error(err)
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 400)

    return () => clearTimeout(timer)
  }, [query])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleClear = () => {
    setQuery('')
    setResults([])
    setSearched(false)
    inputRef.current?.focus()
  }

  const handleAssetClick = (symbol) => {
    navigate(`/asset/${symbol}`)
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl mx-auto w-full">

      {/* Search bar */}
      <div className="relative">
        <SearchIcon
          size={18}
          className="absolute left-4 top-1/2 -translate-y-1/2"
          style={{ color: 'var(--text-muted)' }}
        />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search stocks, ETFs, crypto..."
          className="w-full pl-11 pr-11 py-3.5 rounded-2xl text-sm outline-none border transition-all"
          style={{
            background: 'var(--bg-card)',
            borderColor: query ? 'var(--gold)' : 'var(--border)',
            color: 'var(--text-primary)',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--gold)'}
          onBlur={e => e.target.style.borderColor = query ? 'var(--gold)' : 'var(--border)'}
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full p-0.5 transition-all"
            style={{ color: 'var(--text-muted)' }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <Card className="flex flex-col gap-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />
              <div className="flex-1 flex flex-col gap-1.5">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-3 w-40" />
              </div>
            </div>
          ))}
        </Card>
      )}

      {/* Search results */}
      {!loading && searched && (
        <Card>
          {results.length === 0 ? (
            <div className="flex flex-col items-center py-8 gap-2">
              <SearchIcon size={32} style={{ color: 'var(--text-muted)' }} />
              <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                No results for "{query}"
              </p>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                Try a different symbol or name
              </p>
            </div>
          ) : (
            <>
              <p className="text-xs mb-3" style={{ color: 'var(--text-secondary)' }}>
                {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
              </p>
              <div className="flex flex-col divide-y" style={{ borderColor: 'var(--border)' }}>
                {results.map((asset) => (
                  <div
                    key={`${asset.symbol}-${asset.asset_type}`}
                    className="flex items-center gap-3 py-3 px-2 -mx-2 rounded-xl cursor-pointer transition-all"
                    onClick={() => handleAssetClick(asset.symbol)}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <AssetIcon type={asset.asset_type} symbol={asset.symbol} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {asset.symbol}
                        </p>
                        <TypeBadge type={asset.asset_type} />
                      </div>
                      <p className="text-xs truncate mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                        {asset.name}
                        {asset.exchange && (
                          <span style={{ color: 'var(--text-muted)' }}> · {asset.exchange}</span>
                        )}
                      </p>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '18px' }}>→</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      )}

      {/* Popular assets — shown before searching */}
      {!query && !searched && (
        <>
          <div>
            <p className="text-xs font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
              Popular assets
            </p>
            <Card>
              <div className="flex flex-col divide-y" style={{ borderColor: 'var(--border)' }}>
                {POPULAR.map((asset) => (
                  <div
                    key={asset.symbol}
                    className="flex items-center gap-3 py-3 px-2 -mx-2 rounded-xl cursor-pointer transition-all"
                    onClick={() => handleAssetClick(asset.symbol)}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <AssetIcon type={asset.asset_type} symbol={asset.symbol} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {asset.symbol}
                        </p>
                        <TypeBadge type={asset.asset_type} />
                      </div>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                        {asset.name}
                      </p>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '18px' }}>→</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Filter pills hint */}
          <div className="flex items-center gap-2 flex-wrap">
            {['Stocks', 'ETFs', 'Crypto'].map((label) => (
              <button
                key={label}
                className="px-3 py-1.5 rounded-full text-xs font-medium border transition-all"
                style={{
                  background: 'var(--bg-card)',
                  borderColor: 'var(--border)',
                  color: 'var(--text-secondary)',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--gold)'
                  e.currentTarget.style.color = 'var(--gold)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border)'
                  e.currentTarget.style.color = 'var(--text-secondary)'
                }}
                onClick={() => setQuery(label === 'Crypto' ? 'bitcoin' : label === 'ETFs' ? 'SPY' : 'apple')}
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}

    </div>
  )
}