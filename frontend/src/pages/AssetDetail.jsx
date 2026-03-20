import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Bookmark, BookmarkCheck } from 'lucide-react'
import client from '../api/client'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency, formatCompact, formatPercent } from '../utils/formatters'

// Single fundamental metric card with optional tooltip hint
const FundamentalItem = ({ label, value, hint }) => (
  <div
    className="flex flex-col gap-1 p-3 rounded-xl"
    style={{ background: 'var(--bg-tertiary)' }}
  >
    <div className="flex items-center gap-1">
      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</p>
      {hint && (
        <span
          className="text-xs cursor-help"
          style={{ color: 'var(--text-muted)' }}
          title={hint}
        >
          ℹ️
        </span>
      )}
    </div>
    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
      {value ?? '—'}
    </p>
  </div>
)

export default function AssetDetail() {
  const { symbol } = useParams()
  const navigate = useNavigate()

  const [price, setPrice] = useState(null)
  const [fundamentals, setFundamentals] = useState(null)
  const [inWatchlist, setInWatchlist] = useState(false)
  const [loading, setLoading] = useState(true)
  const [watchlistLoading, setWatchlistLoading] = useState(false)

  // Detect asset type from price response:
  // CoinMarketCap returns market_cap — TwelveData does not
  const isCrypto = Boolean(price?.market_cap)

  // Fetch price + watchlist status on mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        // allSettled — a 502 on price doesn't block the watchlist check
        const [priceRes, watchlistRes] = await Promise.allSettled([
          client.get(`/price/${symbol}`),
          client.get('/watchlist'),
        ])

        if (priceRes.status === 'fulfilled') {
          setPrice(priceRes.value.data)
        }

        if (watchlistRes.status === 'fulfilled') {
          const watchlistSymbols =
            watchlistRes.value.data.items?.map(i => i.symbol) || []
          setInWatchlist(watchlistSymbols.includes(symbol.toUpperCase()))
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [symbol])

  // Fetch extra data once price is available and asset type is known:
  // - Stocks/ETFs → Finnhub fundamentals (P/E, ROE, Beta, etc.)
  // - Crypto → no extra call needed (market_cap/volume already in price response)
  useEffect(() => {
    if (price === null) return // wait for price to load first

    if (isCrypto) {
      // Crypto stats come from CoinMarketCap price response — no extra call needed
      setFundamentals(null)
      return
    }

    // Stocks/ETFs — fetch Finnhub fundamentals
    const fetchFundamentals = async () => {
      try {
        const { data } = await client.get(`/fundamentals/${symbol}`)
        setFundamentals(data)
      } catch {
        // Fundamentals unavailable for this symbol — silently ignore
        setFundamentals(null)
      }
    }
    fetchFundamentals()
  }, [symbol, price, isCrypto])

  const handleWatchlist = async () => {
    setWatchlistLoading(true)
    try {
      if (inWatchlist) {
        await client.delete(`/watchlist/${symbol}`)
        setInWatchlist(false)
      } else {
        await client.post(`/watchlist/${symbol}`)
        setInWatchlist(true)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setWatchlistLoading(false)
    }
  }

  const pricePositive = (price?.change ?? 0) >= 0

  return (
    <div className="flex flex-col gap-6 max-w-3xl">

      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm w-fit transition-all"
        style={{ color: 'var(--text-secondary)' }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
      >
        <ArrowLeft size={16} />
        Back
      </button>

      {/* Price header card */}
      {loading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <Card className="relative overflow-hidden">
          {/* Background accent circle */}
          <div
            className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-5 -translate-y-1/2 translate-x-1/2"
            style={{ background: pricePositive ? 'var(--green)' : 'var(--red)' }}
          />

          <div className="flex items-start justify-between gap-4">
            <div>
              {/* Symbol + market status badge */}
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
                  {symbol.toUpperCase()}
                </h1>
                <span
                  className="px-2 py-0.5 rounded-md text-xs font-medium"
                  style={{
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  {price?.market_status === 'open' ? '🟢 Live' : '🔴 Closed'}
                </span>
              </div>

              {/* Current price + change */}
              {price ? (
                <>
                  <p className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
                    {formatCurrency(price.price)}
                  </p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <Badge value={price.change_pct} />
                    <span
                      className="text-sm"
                      style={{ color: pricePositive ? 'var(--green)' : 'var(--red)' }}
                    >
                      {pricePositive ? '+' : ''}{formatCurrency(price.change)} today
                    </span>
                  </div>
                </>
              ) : (
                <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                  Price unavailable — API rate limit reached
                </p>
              )}
            </div>

            {/* Watchlist toggle button */}
            <button
              onClick={handleWatchlist}
              disabled={watchlistLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all flex-shrink-0"
              style={{
                background: inWatchlist ? 'rgba(245,200,66,0.1)' : 'transparent',
                borderColor: inWatchlist ? 'var(--gold)' : 'var(--border)',
                color: inWatchlist ? 'var(--gold)' : 'var(--text-secondary)',
                cursor: watchlistLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {inWatchlist ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
              {inWatchlist ? 'Saved' : 'Watchlist'}
            </button>
          </div>

          {/* OHLCV row — stocks/ETFs only (crypto doesn't have open/high/low) */}
          {!isCrypto && price?.open > 0 && (
            <div
              className="grid grid-cols-4 gap-3 mt-4 pt-4 border-t"
              style={{ borderColor: 'var(--border)' }}
            >
              {[
                { label: 'Open',   value: formatCurrency(price.open)      },
                { label: 'High',   value: formatCurrency(price.high)      },
                { label: 'Low',    value: formatCurrency(price.low)       },
                { label: 'Volume', value: price.volume?.toLocaleString()  },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</p>
                  <p className="text-sm font-medium mt-0.5" style={{ color: 'var(--text-primary)' }}>
                    {value}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Crypto stats — market cap, 24h volume, 7d change */}
          {isCrypto && price?.market_cap && (
            <div
              className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t"
              style={{ borderColor: 'var(--border)' }}
            >
              {[
                { label: 'Market Cap', value: formatCompact(price.market_cap)    },
                { label: '24h Volume', value: formatCompact(price.volume_24h)    },
                { label: '7d Change',  value: formatPercent(price.change_pct_7d) },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</p>
                  <p className="text-sm font-medium mt-0.5" style={{ color: 'var(--text-primary)' }}>
                    {value}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Action buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button
          className="py-3 rounded-xl text-sm font-semibold transition-all"
          style={{ background: 'var(--gold)', color: '#0A0F1E' }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--gold-light)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--gold)'}
          onClick={() => navigate('/trading')}
        >
          Trade {symbol.toUpperCase()}
        </button>
        <button
          className="py-3 rounded-xl text-sm font-semibold border transition-all"
          style={{
            background: 'transparent',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          onClick={() => navigate('/portfolio')}
        >
          View in portfolio
        </button>
      </div>

      {/* Fundamentals — stocks/ETFs only, not shown for crypto */}
      {!isCrypto && fundamentals && (
        <Card>
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
            Fundamentals
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <FundamentalItem
              label="P/E Ratio"
              value={fundamentals.pe_ratio?.toFixed(2)}
              hint="Price to Earnings — how much investors pay per $1 of earnings"
            />
            <FundamentalItem
              label="P/B Ratio"
              value={fundamentals.pb_ratio?.toFixed(2)}
              hint="Price to Book — market value vs book value"
            />
            <FundamentalItem
              label="ROE"
              value={fundamentals.roe
                ? `${fundamentals.roe.toFixed(1)}%` : null}
              hint="Return on Equity — how efficiently the company uses shareholder funds"
            />
            <FundamentalItem
              label="Net Margin"
              value={fundamentals.net_margin
                ? `${fundamentals.net_margin.toFixed(1)}%` : null}
              hint="Percentage of revenue that becomes profit"
            />
            <FundamentalItem
              label="Beta"
              value={fundamentals.beta?.toFixed(2)}
              hint="Volatility vs market — above 1 means more volatile than S&P 500"
            />
            <FundamentalItem
              label="Div. Yield"
              value={fundamentals.dividend_yield
                ? `${fundamentals.dividend_yield.toFixed(2)}%` : null}
              hint="Annual dividend as percentage of stock price"
            />
            <FundamentalItem
              label="52W High"
              value={formatCurrency(fundamentals.week_52_high)}
              hint="Highest price in the last 52 weeks"
            />
            <FundamentalItem
              label="52W Low"
              value={formatCurrency(fundamentals.week_52_low)}
              hint="Lowest price in the last 52 weeks"
            />
          </div>
        </Card>
      )}

    </div>
  )
}