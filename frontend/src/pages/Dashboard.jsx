import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react'
import useAuthStore from '../store/authStore'
import client from '../api/client'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency, formatPercent, colorClass } from '../utils/formatters'

export default function Dashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const [portfolio, setPortfolio] = useState(null)
  const [marketStatus, setMarketStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.full_name?.split(' ')[0] || 'there'

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [portfolioRes, marketRes] = await Promise.all([
          client.get('/portfolio/me'),
          client.get('/market/status'),
        ])
        setPortfolio(portfolioRes.data)
        setMarketStatus(marketRes.data)
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

      {/* Greeting */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            {greeting}, {firstName} 👋
          </h2>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            Here's your portfolio overview
          </p>
        </div>

        {/* Market status badge */}
        {marketStatus && (
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border"
            style={{
              background: marketStatus.status === 'open'
                ? 'rgba(0,200,150,0.08)' : 'rgba(139,149,168,0.08)',
              borderColor: marketStatus.status === 'open'
                ? 'rgba(0,200,150,0.2)' : 'var(--border)',
              color: marketStatus.status === 'open'
                ? 'var(--green)' : 'var(--text-secondary)',
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: marketStatus.status === 'open'
                  ? 'var(--green)' : 'var(--text-muted)',
              }}
            />
            {marketStatus.status === 'open' ? 'Market open' : 'Market closed'}
          </div>
        )}
      </div>

      {/* Portfolio value hero card */}
      {loading ? (
        <Skeleton className="h-36 w-full" />
      ) : (
        <Card className="relative overflow-hidden">
          {/* Background gold accent */}
          <div
            className="absolute top-0 right-0 w-48 h-48 rounded-full opacity-5 -translate-y-1/2 translate-x-1/2"
            style={{ background: 'var(--gold)' }}
          />
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Total portfolio value
          </p>
          <p className="text-4xl font-bold mt-1" style={{ color: 'var(--text-primary)' }}>
            {formatCurrency(portfolio?.total_value)}
          </p>
          <div className="flex items-center gap-3 mt-2">
            <Badge value={portfolio?.total_pnl_pct} />
            <span
              className="text-sm"
              style={{ color: totalPnlPositive ? 'var(--green)' : 'var(--red)' }}
            >
              {totalPnlPositive ? '+' : ''}{formatCurrency(portfolio?.total_pnl)} all time
            </span>
          </div>
        </Card>
      )}

      {/* Stats row */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              label: 'Total invested',
              value: formatCurrency(portfolio?.total_invested),
              Icon: DollarSign,
              color: 'var(--gold)',
              bg: 'rgba(245,200,66,0.08)',
            },
            {
              label: 'Total P&L',
              value: formatCurrency(portfolio?.total_pnl),
              Icon: totalPnlPositive ? TrendingUp : TrendingDown,
              color: totalPnlPositive ? 'var(--green)' : 'var(--red)',
              bg: totalPnlPositive
                ? 'rgba(0,200,150,0.08)' : 'rgba(255,77,106,0.08)',
            },
            {
              label: 'Holdings',
              value: portfolio?.holdings?.length ?? 0,
              Icon: Activity,
              color: '#818CF8',
              bg: 'rgba(129,140,248,0.08)',
            },
            {
              label: 'Return',
              value: formatPercent(portfolio?.total_pnl_pct),
              Icon: TrendingUp,
              color: totalPnlPositive ? 'var(--green)' : 'var(--red)',
              bg: totalPnlPositive
                ? 'rgba(0,200,150,0.08)' : 'rgba(255,77,106,0.08)',
            },
          ].map(({ label, value, Icon, color, bg }) => (
            <Card key={label} className="flex flex-col gap-2">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: bg }}
              >
                <Icon size={16} style={{ color }} />
              </div>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {label}
              </p>
              <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                {value}
              </p>
            </Card>
          ))}
        </div>
      )}

      {/* Quick link to analytics */}
      <Card
        className="flex items-center justify-between"
        style={{ cursor: 'pointer' }}
        onClick={() => navigate('/analytics')}
      >
        <div>
          <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
            Portfolio performance
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            View historical charts and benchmark comparison
          </p>
        </div>
        <span className="text-lg" style={{ color: 'var(--gold)' }}>→</span>
      </Card>

      {/* Holdings list */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
            Holdings
          </h3>
          <button
            onClick={() => navigate('/portfolio')}
            className="text-xs font-medium"
            style={{ color: 'var(--gold)' }}
          >
            View all →
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col gap-3">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-12" />)}
          </div>
        ) : (
          <div className="flex flex-col divide-y" style={{ borderColor: 'var(--border)' }}>
            {portfolio?.holdings?.slice(0, 5).map((h) => (
              <div
                key={h.symbol}
                className="flex items-center justify-between py-3 rounded-lg px-2 -mx-2"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/asset/${h.symbol}`)}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {/* Left — symbol + name */}
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0"
                    style={{
                      background: h.asset_type === 'crypto'
                        ? 'rgba(245,200,66,0.12)' : 'rgba(129,140,248,0.12)',
                      color: h.asset_type === 'crypto' ? 'var(--gold)' : '#818CF8',
                    }}
                  >
                    {h.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                      {h.symbol}
                    </p>
                    <p
                      className="text-xs truncate max-w-28"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {h.name}
                    </p>
                  </div>
                </div>

                {/* Right — value + P&L */}
                <div className="text-right">
                  <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {formatCurrency(h.current_value)}
                  </p>
                  <p className={`text-xs ${colorClass(h.pnl_pct)}`}>
                    {h.pnl_pct >= 0 ? '+' : ''}{h.pnl_pct.toFixed(2)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

    </div>
  )
}