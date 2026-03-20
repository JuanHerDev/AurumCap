import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Search from './pages/Search'
import Analytics from './pages/Analytics'
import Watchlist from './pages/Watchlist'
import Trading from './pages/Trading'
import AssetDetail from './pages/AssetDetail'
import Layout from './components/layout/Layout'

// Protects routes that require authentication
const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/auth" replace/>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<Auth />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="search" element={<Search />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="watchlist" element={<Watchlist />} />
          <Route path="trading" element={<Trading />} />
          <Route path="asset/:symbol" element={<AssetDetail />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}