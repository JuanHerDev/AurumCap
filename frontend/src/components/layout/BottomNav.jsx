import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, PieChart, Search,
  LineChart, Bookmark, TrendingUp
} from 'lucide-react'

const navItems = [
  { to: '/',          icon: LayoutDashboard, label: 'Home'      },
  { to: '/portfolio', icon: PieChart,         label: 'Portfolio' },
  { to: '/search',    icon: Search,           label: 'Search'    },
  { to: '/analytics', icon: LineChart,        label: 'Analytics' },
  { to: '/watchlist', icon: Bookmark,         label: 'Watchlist' },
]

export default function BottomNav() {
  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around h-16 border-t"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
      }}
    >
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className="flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all"
          style={({ isActive }) => ({
            color: isActive ? 'var(--gold)' : 'var(--text-muted)',
          })}
        >
          <Icon size={20} />
          <span className="text-xs">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}