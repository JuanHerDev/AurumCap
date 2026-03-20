import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bookmark, BookmarkX, TrendingUp, TrendingDown, Plus } from 'lucide-react'
import client from '../api/client'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency } from '../utils/formatters'

export default function Watchlist() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [removing, setRemoving] = useState(null) // symbol being removed

  useEffect(() => {
    const fetchWatchlist = async () => {
      setLoading(true)
      try {
        const { data } = await client.get('/watchlist')
        setItems(data.items || [])
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchWatchlist()
  }, [])

  const handleRemove = async (symbol) => {
    setRemoving(symbol)
    try {
      await client.delete(`/watchlist/${symbol}`)
      setItems(prev => prev.filter(i => i.symbol !== symbol))
    } catch (err) {
      console.error(err)
    } finally {
      setRemoving(null)
    }
  }

  // Empty state
  if (!loading && items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center"
          style={{ background: 'var(--bg-card)' }}
        >
          <Bookmark size={28} style={{ color: 'var(--text-muted)' }} />
        </div>
        <div className="text-center">
          <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
            Your watchlist is empty
          </p>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
            Add assets from Search or Asset Detail
          </p>
        </div>
        <button
          onClick={() => navigate('/search')}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all"
          style={{ background: 'var(--gold)', color: '#0A0F1E' }}
        >
          <Plus size={16} />
          Browse assets
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Watchlist
          </h2>
          {!loading && (
            <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
              {items.length} asset{items.length !== 1 ? 's' : ''} tracked
            </p>
          )}
        </div>
        <button
          onClick={() => navigate('/search')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all"
          style={{
            background: 'transparent',
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
        >
          <Plus size={15} />
          Add asset
        </button>
      </div>

      {/* List */}
      <Card>
        {loading ? (
          <div className="flex flex-col gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />
                <div className="flex-1 flex flex-col gap-1.5">
                  <Skeleton className="h-3.5 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <div className="flex flex-col gap-1.5 items-end">
                  <Skeleton className="h-3.5 w-20" />
                  <Skeleton className="h-3 w-14" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col divide-y" style={{ borderColor: 'var(--border)' }}>
            {items.map((item) => {
              const positive = (item.change_pct ?? 0) >= 0
              const isRemoving = removing === item.symbol

              return (
                <div
                  key={item.symbol}
                  className="flex items-center gap-3 py-3 px-2 -mx-2 rounded-xl transition-all"
                  style={{ opacity: isRemoving ? 0.5 : 1 }}
                >
                  {/* Asset icon */}
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 cursor-pointer"
                    style={{
                      background: item.asset_type === 'crypto'
                        ? 'rgba(245,200,66,0.12)' : 'rgba(129,140,248,0.12)',
                      color: item.asset_type === 'crypto' ? 'var(--gold)' : '#818CF8',
                    }}
                    onClick={() => navigate(`/asset/${item.symbol}`)}
                  >
                    {item.symbol.slice(0, 2)}
                  </div>

                  {/* Symbol + name */}
                  <div
                    className="flex-1 min-w-0 cursor-pointer"
                    onClick={() => navigate(`/asset/${item.symbol}`)}
                  >
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {item.symbol}
                      </p>
                      <span
                        className="px-1.5 py-0.5 rounded text-xs font-medium hidden sm:block"
                        style={{
                          background: item.asset_type === 'crypto'
                            ? 'rgba(245,200,66,0.1)' : 'rgba(129,140,248,0.1)',
                          color: item.asset_type === 'crypto'
                            ? 'var(--gold)' : '#818CF8',
                        }}
                      >
                        {item.asset_type === 'crypto' ? 'Crypto'
                          : item.asset_type === 'etf' ? 'ETF' : 'Stock'}
                      </span>
                    </div>
                    <p
                      className="text-xs truncate mt-0.5"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {item.name}
                    </p>
                  </div>

                  {/* Price + change */}
                  <div
                    className="text-right cursor-pointer"
                    onClick={() => navigate(`/asset/${item.symbol}`)}
                  >
                    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {item.current_price
                        ? formatCurrency(item.current_price)
                        : '—'}
                    </p>
                    {item.change_pct !== undefined && item.change_pct !== null ? (
                      <div className="flex items-center justify-end gap-1 mt-0.5">
                        {positive
                          ? <TrendingUp size={11} style={{ color: 'var(--green)' }} />
                          : <TrendingDown size={11} style={{ color: 'var(--red)' }} />
                        }
                        <span
                          className="text-xs font-medium"
                          style={{ color: positive ? 'var(--green)' : 'var(--red)' }}
                        >
                          {positive ? '+' : ''}{item.change_pct.toFixed(2)}%
                        </span>
                      </div>
                    ) : (
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                        —
                      </p>
                    )}
                  </div>

                  {/* Remove button */}
                  <button
                    onClick={() => handleRemove(item.symbol)}
                    disabled={isRemoving}
                    className="ml-2 p-2 rounded-lg transition-all flex-shrink-0"
                    style={{
                      color: 'var(--text-muted)',
                      cursor: isRemoving ? 'not-allowed' : 'pointer',
                    }}
                    onMouseEnter={e => {
                      if (!isRemoving) {
                        e.currentTarget.style.background = 'rgba(255,77,106,0.1)'
                        e.currentTarget.style.color = 'var(--red)'
                      }
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = 'transparent'
                      e.currentTarget.style.color = 'var(--text-muted)'
                    }}
                    title="Remove from watchlist"
                  >
                    <BookmarkX size={16} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </Card>

    </div>
  )
}