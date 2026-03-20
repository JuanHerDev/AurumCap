import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, PieChart, Search,
  LineChart, Bookmark, TrendingUp, LogOut
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import useTheme from '../../hooks/useTheme'
import { Sun, Moon } from 'lucide-react'

const navItems = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard'  },
  { to: '/portfolio', icon: PieChart,         label: 'Portfolio'  },
  { to: '/search',    icon: Search,           label: 'Search'     },
  { to: '/analytics', icon: LineChart,        label: 'Analytics'  },
  { to: '/watchlist', icon: Bookmark,         label: 'Watchlist'  },
  { to: '/trading',   icon: TrendingUp,       label: 'Trading'    },
]

export default function Sidebar() {
  const { logout } = useAuthStore()
  const { theme, toggleTheme } = useTheme()

  return (
    <aside
      className="hidden lg:flex flex-col fixed top-0 left-0 h-full w-64 z-40 border-r"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-6 border-b" style={{ borderColor: 'var(--border)' }}>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
          style={{ background: 'var(--gold)', color: '#0A0F1E' }}
        >
          A
        </div>
        <span className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>
          AurumCap
        </span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive ? 'active-nav' : 'inactive-nav'
              }`
            }
            style={({ isActive }) => ({
              background: isActive ? 'rgba(245, 200, 66, 0.1)' : 'transparent',
              color: isActive ? 'var(--gold)' : 'var(--text-secondary)',
            })}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom actions */}
      <div className="px-3 py-4 border-t flex flex-col gap-1" style={{ borderColor: 'var(--border)' }}>
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium w-full transition-all duration-150"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          {theme === 'dark' ? 'Light mode' : 'Dark mode'}
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium w-full transition-all duration-150"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <LogOut size={18} />
          Sign out
        </button>
      </div>
    </aside>
  )
}