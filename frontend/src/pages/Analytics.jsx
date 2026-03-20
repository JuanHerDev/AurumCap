import { useEffect, useState } from 'react'
import {
  ResponsiveContainer, AreaChart, Area,
  XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts'
import { analyticsClient } from '../api/client'
import Card from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency, formatPercent } from '../utils/formatters'

const RANGES = ['1W', '1M', '3M', '1Y', 'ALL']

const COLORS = [
  '#F5C842', '#00C896', '#818CF8', '#FF4D6A',
  '#38BDF8', '#FB923C', '#A78BFA', '#34D399',
]

// Custom tooltip for portfolio history chart
const HistoryTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const pnl = payload[0]?.payload?.pnl ?? 0
  const positive = pnl >= 0
  return (
    <div
      className="px-3 py-2 rounded-xl border text-xs"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
        color: 'var(--text-primary)',
      }}
    >
      <p style={{ color: 'var(--text-secondary)' }}>{label}</p>
      <p className="font-semibold mt-0.5">{formatCurrency(payload[0]?.value)}</p>
      <p style={{ color: positive ? 'var(--green)' : 'var(--red)' }}>
        {positive ? '+' : ''}{formatCurrency(pnl)}
      </p>
    </div>
  )
}

// Skeleton loading state with descriptive message
const ChartLoading = ({ message = 'Loading data...' }) => (
  <div className="h-56 flex flex-col items-center justify-center gap-3">
    <Skeleton className="h-3 w-3/4" />
    <Skeleton className="h-3 w-1/2" />
    <Skeleton className="h-3 w-2/3" />
    <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
      {message}
    </p>
  </div>
)

export default function Analytics() {
  const [range, setRange] = useState('1M')
  const [history, setHistory] = useState([])
  const [allocation, setAllocation] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [allocationLoading, setAllocationLoading] = useState(true)

  // Sequential loading — allocation first (fast), then history (rate-limited)
  // Sequential prevents concurrent TwelveData calls from exhausting
  // the 8 credits/min free plan limit. Cache (1h) makes subsequent
  // loads instant.
  useEffect(() => {
    const fetchAll = async () => {
      setHistoryLoading(true)
      setAllocationLoading(true)
      setHistory([])
      setAllocation(null)

      // Step 1 — Allocation (current prices, fastest)
      try {
        const { data } = await analyticsClient.get(
          '/analytics/portfolio/allocation'
        )
        setAllocation(data)
      } catch (err) {
        console.error('[Analytics] Allocation error:', err)
      } finally {
        setAllocationLoading(false)
      }

      // Step 2 — Portfolio history (historical prices, rate-limited)
      // Cached for 1h after first load
      try {
        const { data } = await analyticsClient.get(
          `/analytics/portfolio/history?range=${range}`
        )
        setHistory(
          data.snapshots.map(s => ({
            date: new Date(s.date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }),
            value: s.total_value,
            invested: s.total_invested,
            pnl: s.pnl,
            pnl_pct: s.pnl_pct,
          }))
        )
      } catch (err) {
        console.error('[Analytics] History error:', err)
        setHistory([])
      } finally {
        setHistoryLoading(false)
      }
    }

    fetchAll()
  }, [range])

  // Derived stats from history array
  const firstValue   = history[0]?.value
  const lastValue    = history[history.length - 1]?.value
  const lastPnl      = history[history.length - 1]?.pnl ?? 0
  const lastInvested = history[history.length - 1]?.invested ?? 0
  const periodReturn = firstValue
    ? ((lastValue - firstValue) / firstValue * 100)
    : null

  return (
    <div className="flex flex-col gap-6">

      {/* Range selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {RANGES.map((r) => (
          <button
            key={r}
            onClick={() => setRange(r)}
            className="px-4 py-1.5 rounded-xl text-sm font-medium transition-all border"
            style={{
              background: range === r ? 'rgba(245,200,66,0.1)' : 'transparent',
              borderColor: range === r ? 'var(--gold)' : 'var(--border)',
              color: range === r ? 'var(--gold)' : 'var(--text-secondary)',
            }}
          >
            {r}
          </button>
        ))}
      </div>

      {/* Period summary stat cards */}
      {!historyLoading && history.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              label: 'Current value',
              value: formatCurrency(lastValue),
              color: 'var(--text-primary)',
            },
            {
              label: 'Period return',
              value: formatPercent(periodReturn),
              color: (periodReturn ?? 0) >= 0 ? 'var(--green)' : 'var(--red)',
            },
            {
              label: 'Total invested',
              value: formatCurrency(lastInvested),
              color: 'var(--text-primary)',
            },
            {
              label: 'Total P&L',
              value: formatCurrency(lastPnl),
              color: lastPnl >= 0 ? 'var(--green)' : 'var(--red)',
            },
          ].map(({ label, value, color }) => (
            <Card key={label} className="flex flex-col gap-1">
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {label}
              </p>
              <p className="text-lg font-semibold" style={{ color }}>
                {value}
              </p>
            </Card>
          ))}
        </div>
      )}

      {/* Portfolio value history — area chart */}
      <Card>
        <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
          Portfolio value
        </h3>

        {historyLoading ? (
          <ChartLoading message="Fetching historical prices — cached for 1h after first load..." />
        ) : history.length === 0 ? (
          <div
            className="h-56 flex items-center justify-center text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            No data available for this range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={history} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="valueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="var(--gold)" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="var(--gold)" stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
                width={45}
              />
              <Tooltip content={<HistoryTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="var(--gold)"
                strokeWidth={2}
                fill="url(#valueGradient)"
                dot={false}
                activeDot={{ r: 4, fill: 'var(--gold)', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Card>

      {/* Asset allocation — horizontal progress bars */}
      <Card>
        <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
          Current allocation
        </h3>

        {allocationLoading ? (
          <div className="flex flex-col gap-3">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-5" />)}
          </div>
        ) : !allocation ? (
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Allocation data unavailable
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {allocation.allocations.map((a, i) => {
              const color = COLORS[i % COLORS.length]
              return (
                <div key={a.symbol} className="flex items-center gap-3">
                  {/* Color dot */}
                  <div
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ background: color }}
                  />
                  {/* Symbol */}
                  <span
                    className="text-sm font-medium w-12 flex-shrink-0"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    {a.symbol}
                  </span>
                  {/* Progress bar */}
                  <div
                    className="flex-1 h-1.5 rounded-full overflow-hidden"
                    style={{ background: 'var(--bg-tertiary)' }}
                  >
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${a.allocation_pct}%`, background: color }}
                    />
                  </div>
                  {/* Percentage */}
                  <span
                    className="text-xs w-12 text-right flex-shrink-0"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    {a.allocation_pct.toFixed(1)}%
                  </span>
                  {/* Value — desktop only */}
                  <span
                    className="text-xs w-20 text-right flex-shrink-0 hidden lg:block"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {formatCurrency(a.current_value)}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </Card>

    </div>
  )
}