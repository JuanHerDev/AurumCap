import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { TrendingUp, TrendingDown, ArrowLeftRight } from 'lucide-react'
import client from '../api/client'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency, formatCryptoPrice, colorClass } from '../utils/formatters'

// Trade type tab button
const TradeTab = ({ label, active, onClick, color }) => (
  <button
    onClick={onClick}
    className="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all border"
    style={{
      background: active ? `${color}18` : 'transparent',
      borderColor: active ? color : 'var(--border)',
      color: active ? color : 'var(--text-secondary)',
    }}
  >
    {label}
  </button>
)

// Order summary row
const SummaryRow = ({ label, value, highlight }) => (
  <div className="flex items-center justify-between py-1.5">
    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
    <span
      className="text-xs font-semibold"
      style={{ color: highlight ? 'var(--gold)' : 'var(--text-primary)' }}
    >
      {value}
    </span>
  </div>
)

export default function Trading() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Pre-fill symbol from query param: /trading?symbol=AAPL
  const [symbol, setSymbol] = useState(
    searchParams.get('symbol')?.toUpperCase() || ''
  )
  const [symbolInput, setSymbolInput] = useState(
    searchParams.get('symbol')?.toUpperCase() || ''
  )

  const [side, setSide] = useState('BUY')        // BUY | SELL
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState(null)
  const [holdings, setHoldings] = useState([])
  const [priceLoading, setPriceLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(null)   // success message
  const [error, setError] = useState(null)       // error message

  // Fetch live price when symbol changes
  useEffect(() => {
    if (!symbol) return
    const fetchPrice = async () => {
      setPriceLoading(true)
      setPrice(null)
      setError(null)
      try {
        const { data } = await client.get(`/price/${symbol}`)
        setPrice(data)
      } catch {
        setError(`Could not fetch price for ${symbol}`)
      } finally {
        setPriceLoading(false)
      }
    }
    fetchPrice()
  }, [symbol])

  // Fetch current holdings to show existing position
  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        const { data } = await client.get('/portfolio/me')
        setHoldings(data.holdings || [])
      } catch {
        // Non-critical — silently ignore
      }
    }
    fetchHoldings()
  }, [])

  // Find existing holding for current symbol
  const existingHolding = holdings.find(
    h => h.symbol === symbol.toUpperCase()
  )

  // Total order value
  const qty = parseFloat(quantity) || 0
  const currentPrice = price?.price || 0
  const totalValue = qty * currentPrice

  // Validate the order before submitting
  const getValidationError = () => {
    if (!symbol) return 'Enter a symbol'
    if (!price) return 'Price not available'
    if (!quantity || qty <= 0) return 'Enter a valid quantity'
    if (side === 'SELL' && existingHolding && qty > existingHolding.quantity) {
      return `You only hold ${existingHolding.quantity} ${symbol}`
    }
    if (side === 'SELL' && !existingHolding) {
      return `You don't hold any ${symbol}`
    }
    return null
  }

  const validationError = getValidationError()

  const handleSymbolSearch = (e) => {
    e.preventDefault()
    const s = symbolInput.trim().toUpperCase()
    if (s) setSymbol(s)
  }

  const handleSubmit = async () => {
  if (validationError) return
  setSubmitting(true)
  setError(null)
  setSuccess(null)

  try {
      // Step 1 — resolve asset_id from symbol via search endpoint
      const searchRes = await client.get(`/search?q=${symbol}&limit=1`)
      const asset = searchRes.data.results?.[0]

      if (!asset) {
        setError(`Asset '${symbol}' not found in database`)
        return
      }

      // Step 2 — submit transaction with correct schema fields
      await client.post('/transactions', {
        asset_id: asset.id,
        type: side,               // "BUY" | "SELL"
        quantity: qty,
        price: currentPrice,
        fees: 0,
        date: new Date().toISOString(),
      })

      setSuccess(
        `${side === 'BUY' ? 'Bought' : 'Sold'} ${qty} ${symbol} at ${formatCurrency(currentPrice)}`
      )
      setQuantity('')

      // Refresh holdings after successful trade
      const { data } = await client.get('/portfolio/me')
      setHoldings(data.holdings || [])

    } catch (err) {
      setError(
        err.response?.data?.detail || 'Transaction failed — please try again'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-lg">

      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Trade
        </h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
          Buy and sell stocks, ETFs and crypto
        </p>
      </div>

      {/* Symbol search */}
      <Card>
        <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
          Asset
        </p>
        <form onSubmit={handleSymbolSearch} className="flex gap-2">
          <input
            type="text"
            value={symbolInput}
            onChange={e => setSymbolInput(e.target.value.toUpperCase())}
            placeholder="AAPL, BTC, QQQ..."
            className="flex-1 px-3 py-2.5 rounded-xl text-sm outline-none border transition-all"
            style={{
              background: 'var(--bg-tertiary)',
              borderColor: 'var(--border)',
              color: 'var(--text-primary)',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--gold)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
          />
          <button
            type="submit"
            className="px-4 py-2.5 rounded-xl text-sm font-semibold transition-all"
            style={{ background: 'var(--gold)', color: '#0A0F1E' }}
          >
            Search
          </button>
        </form>

        {/* Live price display */}
        {symbol && (
          <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
            {priceLoading ? (
              <div className="flex items-center gap-3">
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-5 w-16" />
              </div>
            ) : price ? (
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
                      {symbol}
                    </p>
                    <span
                      className="text-xs px-1.5 py-0.5 rounded"
                      style={{
                        background: 'var(--bg-tertiary)',
                        color: 'var(--text-muted)',
                      }}
                    >
                      {price.market_status === 'open' ? '🟢 Live' : '🔴 Closed'}
                    </span>
                  </div>
                  <p className="text-2xl font-bold mt-0.5" style={{ color: 'var(--text-primary)' }}>
                    {formatCurrency(price.price)}
                  </p>
                </div>
                <div className="text-right">
                  <Badge value={price.change_pct} />
                  <p
                    className="text-xs mt-1"
                    style={{
                      color: (price.change ?? 0) >= 0 ? 'var(--green)' : 'var(--red)',
                    }}
                  >
                    {(price.change ?? 0) >= 0 ? '+' : ''}{formatCurrency(price.change)} today
                  </p>
                </div>
              </div>
            ) : error ? (
              <p className="text-sm" style={{ color: 'var(--red)' }}>{error}</p>
            ) : null}
          </div>
        )}
      </Card>

      {/* Existing position — show if user holds this asset */}
      {existingHolding && (
        <Card>
          <p className="text-xs font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
            Your position
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Quantity',   value: existingHolding.quantity },
              { label: 'Avg. price', value: formatCurrency(existingHolding.avg_price) },
              { label: 'P&L',        value: formatCurrency(existingHolding.pnl),
                color: (existingHolding.pnl ?? 0) >= 0 ? 'var(--green)' : 'var(--red)' },
            ].map(({ label, value, color }) => (
              <div key={label}>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</p>
                <p
                  className="text-sm font-semibold mt-0.5"
                  style={{ color: color || 'var(--text-primary)' }}
                >
                  {value}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Order form */}
      {symbol && price && (
        <Card>
          {/* BUY / SELL tabs */}
          <div className="flex gap-2 mb-5">
            <TradeTab
              label="Buy"
              active={side === 'BUY'}
              onClick={() => { setSide('BUY'); setError(null); setSuccess(null) }}
              color="var(--green)"
            />
            <TradeTab
              label="Sell"
              active={side === 'SELL'}
              onClick={() => { setSide('SELL'); setError(null); setSuccess(null) }}
              color="var(--red)"
            />
          </div>

          {/* Quantity input */}
          <div className="flex flex-col gap-1.5 mb-4">
            <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
              Quantity
            </label>
            <input
              type="number"
              min="0"
              step="any"
              value={quantity}
              onChange={e => {
                setQuantity(e.target.value)
                setError(null)
                setSuccess(null)
              }}
              placeholder="0.00"
              className="px-3 py-2.5 rounded-xl text-sm outline-none border transition-all"
              style={{
                background: 'var(--bg-tertiary)',
                borderColor: 'var(--border)',
                color: 'var(--text-primary)',
              }}
              onFocus={e => e.target.style.borderColor = 'var(--gold)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
            {/* Quick quantity buttons for stocks */}
            {!price.market_cap && existingHolding && side === 'SELL' && (
              <div className="flex gap-2 mt-1">
                {[0.25, 0.5, 0.75, 1].map(pct => (
                  <button
                    key={pct}
                    onClick={() => setQuantity(
                      (existingHolding.quantity * pct).toFixed(4)
                    )}
                    className="flex-1 py-1 rounded-lg text-xs font-medium border transition-all"
                    style={{
                      background: 'var(--bg-tertiary)',
                      borderColor: 'var(--border)',
                      color: 'var(--text-secondary)',
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--red)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                  >
                    {pct * 100}%
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Order summary */}
          {qty > 0 && (
            <div
              className="rounded-xl p-3 mb-4"
              style={{ background: 'var(--bg-tertiary)' }}
            >
              <SummaryRow
                label="Price per unit"
                value={formatCurrency(currentPrice)}
              />
              <SummaryRow
                label="Quantity"
                value={qty}
              />
              <div
                className="border-t my-1.5"
                style={{ borderColor: 'var(--border)' }}
              />
              <SummaryRow
                label="Total value"
                value={formatCurrency(totalValue)}
                highlight
              />
            </div>
          )}

          {/* Success message */}
          {success && (
            <div
              className="flex items-center gap-2 px-3 py-2.5 rounded-xl mb-3 text-sm"
              style={{
                background: 'rgba(0,200,150,0.1)',
                color: 'var(--green)',
                border: '1px solid rgba(0,200,150,0.2)',
              }}
            >
              ✓ {success}
            </div>
          )}

          {/* Validation / API error */}
          {error && !success && (
            <div
              className="flex items-center gap-2 px-3 py-2.5 rounded-xl mb-3 text-sm"
              style={{
                background: 'rgba(255,77,106,0.1)',
                color: 'var(--red)',
                border: '1px solid rgba(255,77,106,0.2)',
              }}
            >
              {error}
            </div>
          )}

          {/* Submit button */}
          <button
            onClick={handleSubmit}
            disabled={!!validationError || submitting}
            className="w-full py-3 rounded-xl text-sm font-semibold transition-all"
            style={{
              background: validationError || submitting
                ? 'var(--bg-tertiary)'
                : side === 'BUY' ? 'var(--green)' : 'var(--red)',
              color: validationError || submitting
                ? 'var(--text-muted)'
                : '#0A0F1E',
              cursor: validationError || submitting ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting
              ? 'Processing...'
              : validationError
              ? validationError
              : `${side === 'BUY' ? 'Buy' : 'Sell'} ${symbol}`
            }
          </button>
        </Card>
      )}

      {/* Recent transactions link */}
      <button
        onClick={() => navigate('/portfolio')}
        className="flex items-center justify-center gap-2 text-sm transition-all"
        style={{ color: 'var(--text-secondary)' }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
      >
        <ArrowLeftRight size={14} />
        View portfolio
      </button>

    </div>
  )
}