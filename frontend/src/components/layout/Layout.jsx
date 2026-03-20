import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'
import TopBar from './TopBar'
import { useEffect } from 'react'
import useAuthStore from '../../store/authStore'

export default function Layout() {
  const { fetchUser } = useAuthStore()

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Sidebar — fixed, visible only on desktop (lg+) */}
      <Sidebar />

      {/* Main content — takes remaining width after sidebar */}
      <div className="flex flex-col flex-1 min-w-0 lg:ml-64">
        <TopBar />
        <main className="flex-1 min-w-0 p-4 lg:p-8 pb-24 lg:pb-8">
          <Outlet />
        </main>
      </div>

      {/* Bottom nav — fixed, visible only on mobile */}
      <BottomNav />
    </div>
  )
}