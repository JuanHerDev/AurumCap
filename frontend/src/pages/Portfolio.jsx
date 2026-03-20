import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import client from '../api/client'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency, formatPercent, colorClass } from '../utils/formatters'

// Colores para el donut chart
const CHART_COLORS = [
  '#F5C842', '#00C896', '#818CF8', '#FF4D6A',
  '#38BDF8', '#FB923C', '#A78BFA', '#34D399',
]

// Tooltip personalizado del donut
const DonutTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div
      className="px-3 py-2 rounded-xl border text-xs"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
        color: 'var(--text-primary)',
      }}
    >
      <p className="font-semibold">{d.name}</p>
      <p style={{ color: 'var(--text-secondary)' }}>
        {formatCurrency(d.value)} · {d.payload.allocation_pct.toFixed(1)}%
      </p>
    </div>
  )
}

export default function Portfolio() {
  const navigate = useNavigate()
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeIndex, setActiveIndex] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data } = await client.get('/portfolio/me')
        setPortfolio(data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const totalPnlPositive = portfolio?.total_pnl >= 0

  return (
    <div className="flex flex-col gap-6">

      {/* Header stats */}
      {loading ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <Card className="relative overflow-hidden">
          <div
            className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-5 -translate-y-1/2 translate-x-1/2"
            style={{ background: 'var(--gold)' }}
          />
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Total portfolio value
              </p>
              <p className="text-3xl font-bold mt-1" style={{ color: 'var(--text-primary)' }}>
                {formatCurrency(portfolio?.total_value)}
              </p>
              <div className="flex items-center gap-3 mt-1.5">
                <Badge value={portfolio?.total_pnl_pct} />
                <span
                  className="text-sm"
                  style={{ color: totalPnlPositive ? 'var(--green)' : 'var(--red)' }}
                >
                  {totalPnlPositive ? '+' : ''}{formatCurrency(portfolio?.total_pnl)} all time
                </span>
              </div>
            </div>

            {/* Secondary stats */}
            <div className="flex gap-6">
              <div>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  Invested
                </p>
                <p className="text-lg font-semibold mt-0.5" style={{ color: 'var(--text-primary)' }}>
                  {formatCurrency(portfolio?.total_invested)}
                </p>
              </div>
              <div>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  Holdings
                </p>
                <p className="text-lg font-semibold mt-0.5" style={{ color: 'var(--text-primary)' }}>
                  {portfolio?.holdings?.length ?? 0}
                </p>
              </div>
              <div>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  Return
                </p>
                <p
                  className="text-lg font-semibold mt-0.5"
                  style={{ color: totalPnlPositive ? 'var(--green)' : 'var(--red)' }}
                >
                  {formatPercent(portfolio?.total_pnl_pct)}
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Donut chart + allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Donut chart */}
        <Card>
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
            Asset allocation
          </h3>
          {loading ? (
            <Skeleton className="h-56 w-full" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={portfolio?.holdings}
                  dataKey="current_value"
                  nameKey="symbol"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  onMouseEnter={(_, index) => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(null)}
                >
                  {portfolio?.holdings?.map((entry, index) => (
                    <Cell
                      key={entry.symbol}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                      opacity={activeIndex === null || activeIndex === index ? 1 : 0.4}
                      stroke="none"
                    />
                  ))}
                </Pie>
                <Tooltip content={<DonutTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Allocation list */}
        <Card>
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
            Breakdown
          </h3>
          {loading ? (
            <div className="flex flex-col gap-3">
              {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-8" />)}
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {portfolio?.holdings?.map((h, index) => (
                <div key={h.symbol} className="flex items-center gap-3">
                  {/* Color dot */}
                  <div
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ background: CHART_COLORS[index % CHART_COLORS.length] }}
                  />
                  {/* Symbol */}
                  <span
                    className="text-sm font-medium w-12 flex-shrink-0"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    {h.symbol}
                  </span>
                  {/* Progress bar */}
                  <div
                    className="flex-1 h-1.5 rounded-full overflow-hidden"
                    style={{ background: 'var(--bg-tertiary)' }}
                  >
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${h.allocation_pct}%`,
                        background: CHART_COLORS[index % CHART_COLORS.length],
                      }}
                    />
                  </div>
                  {/* Percentage */}
                  <span
                    className="text-xs w-10 text-right flex-shrink-0"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    {h.allocation_pct.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Holdings table */}
      <Card>
        <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
          All holdings
        </h3>

        {loading ? (
          <div className="flex flex-col gap-3">
            {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : (
          <>
            {/* Table header — desktop only */}
            <div
              className="hidden lg:grid grid-cols-6 gap-4 px-3 pb-2 text-xs font-medium border-b mb-1"
              style={{
                color: 'var(--text-muted)',
                borderColor: 'var(--border)',
              }}
            >
              <span className="col-span-2">Asset</span>
              <span className="text-right">Price</span>
              <span className="text-right">Value</span>
              <span className="text-right">P&L</span>
              <span className="text-right">Return</span>
            </div>

            {/* Holdings rows */}
            <div className="flex flex-col divide-y" style={{ borderColor: 'var(--border)' }}>
              {portfolio?.holdings?.map((h, index) => (
                <div
                  key={h.symbol}
                  className="py-3 px-3 -mx-3 rounded-lg cursor-pointer transition-all"
                  onClick={() => navigate(`/asset/${h.symbol}`)}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Mobile layout */}
                  <div className="lg:hidden flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0"
                        style={{
                          background: `${CHART_COLORS[index % CHART_COLORS.length]}18`,
                          color: CHART_COLORS[index % CHART_COLORS.length],
                        }}
                      >
                        {h.symbol.slice(0, 2)}
                      </div>
                      <div>
                        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {h.symbol}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                          {h.quantity} @ {formatCurrency(h.avg_price)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                        {formatCurrency(h.current_value)}
                      </p>
                      <p className={`text-xs ${colorClass(h.pnl_pct)}`}>
                        {h.pnl_pct >= 0 ? '+' : ''}{h.pnl_pct.toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {/* Desktop layout */}
                  <div className="hidden lg:grid grid-cols-6 gap-4 items-center">
                    {/* Asset */}
                    <div className="col-span-2 flex items-center gap-3">
                      <div
                        className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0"
                        style={{
                          background: `${CHART_COLORS[index % CHART_COLORS.length]}18`,
                          color: CHART_COLORS[index % CHART_COLORS.length],
                        }}
                      >
                        {h.symbol.slice(0, 2)}
                      </div>
                      <div>
                        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {h.symbol}
                        </p>
                        <p
                          className="text-xs truncate max-w-36"
                          style={{ color: 'var(--text-secondary)' }}
                        >
                          {h.name}
                        </p>
                      </div>
                    </div>

                    {/* Current price */}
                    <p className="text-sm text-right" style={{ color: 'var(--text-primary)' }}>
                      {formatCurrency(h.current_price)}
                    </p>

                    {/* Current value */}
                    <p className="text-sm font-medium text-right" style={{ color: 'var(--text-primary)' }}>
                      {formatCurrency(h.current_value)}
                    </p>

                    {/* P&L absolute */}
                    <p className={`text-sm text-right ${colorClass(h.pnl)}`}>
                      {h.pnl >= 0 ? '+' : ''}{formatCurrency(h.pnl)}
                    </p>

                    {/* P&L % */}
                    <div className="flex justify-end">
                      <Badge value={h.pnl_pct} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>

      {/* Last updated */}
      {portfolio?.last_updated && (
        <p className="text-center text-xs" style={{ color: 'var(--text-muted)' }}>
          Last updated: {new Date(portfolio.last_updated).toLocaleTimeString()}
        </p>
      )}

    </div>
  )
}