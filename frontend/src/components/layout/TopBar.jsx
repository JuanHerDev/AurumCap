import { useLocation } from 'react-router-dom'
import { Bell } from 'lucide-react'
import useAuthStore from '../../store/authStore'

const pageTitles = {
  '/':          'Dashboard',
  '/portfolio': 'Portfolio',
  '/search':    'Search',
  '/analytics': 'Analytics',
  '/watchlist': 'Watchlist',
  '/trading':   'Trading',
}

export default function TopBar() {
  const { pathname } = useLocation()
  const { user } = useAuthStore()

  const title = pageTitles[pathname] || 'AurumCap'
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.full_name?.split(' ')[0] || 'there'

  return (
    <header
      className="sticky top-0 z-30 flex items-center justify-between px-4 lg:px-8 h-16 border-b"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
      }}
    >
      {/* Left — greeting on mobile, page title on desktop */}
      <div>
        <p className="text-xs lg:hidden" style={{ color: 'var(--text-secondary)' }}>
          {greeting}, {firstName} 👋
        </p>
        <h1 className="font-semibold text-base lg:text-lg" style={{ color: 'var(--text-primary)' }}>
          {title}
        </h1>
      </div>

      {/* Right — logo on mobile, actions on all */}
      <div className="flex items-center gap-3">
        {/* Logo — mobile only */}
        <div
          className="lg:hidden w-7 h-7 rounded-md flex items-center justify-center font-bold text-xs"
          style={{ background: 'var(--gold)', color: '#0A0F1E' }}
        >
          A
        </div>

        {/* Notification bell */}
        <button
          className="w-9 h-9 rounded-lg flex items-center justify-center transition-all"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <Bell size={18} />
        </button>

        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold"
          style={{ background: 'rgba(245,200,66,0.15)', color: 'var(--gold)' }}
        >
          {firstName[0]?.toUpperCase()}
        </div>
      </div>
    </header>
  )
}