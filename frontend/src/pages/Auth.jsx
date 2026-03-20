import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, TrendingUp } from 'lucide-react'
import useAuthStore from '../store/authStore'

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ email: '', password: '', fullName: '' })
  const [showPassword, setShowPassword] = useState(false)

  const { login, register, isLoading, error, isAuthenticated, clearError } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  useEffect(() => {
    clearError()
  }, [mode, clearError])

  const handleSubmit = async (e) => {
    e.preventDefault()
    let success
    if (mode === 'login') {
      success = await login(form.email, form.password)
    } else {
      success = await register(form.email, form.password, form.fullName)
    }
    if (success) navigate('/', { replace: true })
  }

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'var(--bg-primary)' }}
    >
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="flex flex-col items-center gap-3 mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg"
            style={{ background: 'var(--gold)' }}
          >
            <TrendingUp size={26} color="#0A0F1E" strokeWidth={2.5} />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              AurumCap
            </h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
              Your personal investment tracker
            </p>
          </div>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl p-8 border"
          style={{
            background: 'var(--bg-card)',
            borderColor: 'var(--border)',
          }}
        >
          {/* Tabs */}
          <div
            className="flex rounded-xl p-1 mb-6"
            style={{ background: 'var(--bg-primary)' }}
          >
            {['login', 'register'].map((tab) => (
              <button
                key={tab}
                onClick={() => setMode(tab)}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium capitalize transition-all duration-200"
                style={{
                  background: mode === tab ? 'var(--bg-card)' : 'transparent',
                  color: mode === tab ? 'var(--text-primary)' : 'var(--text-muted)',
                  boxShadow: mode === tab ? '0 1px 4px rgba(0,0,0,0.4)' : 'none',
                  border: mode === tab ? '1px solid var(--border-light)' : '1px solid transparent',
                }}
              >
                {tab === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">

            {/* Full name — register only */}
            {mode === 'register' && (
              <div className="flex flex-col gap-2">
                <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                  Full name
                </label>
                <input
                  type="text"
                  name="fullName"
                  value={form.fullName}
                  onChange={handleChange}
                  placeholder="Jhon Doe"
                  className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all border"
                  style={{
                    background: 'var(--bg-primary)',
                    borderColor: 'var(--border-light)',
                    color: 'var(--text-primary)',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--gold)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border-light)'}
                />
              </div>
            )}

            {/* Email */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                Email
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
                className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all border"
                style={{
                  background: 'var(--bg-primary)',
                  borderColor: 'var(--border-light)',
                  color: 'var(--text-primary)',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--gold)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-light)'}
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  required
                  className="w-full px-4 py-3 pr-12 rounded-xl text-sm outline-none transition-all border"
                  style={{
                    background: 'var(--bg-primary)',
                    borderColor: 'var(--border-light)',
                    color: 'var(--text-primary)',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--gold)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border-light)'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-all"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseEnter={e => e.currentTarget.style.color = 'var(--text-secondary)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div
                className="px-4 py-3 rounded-xl text-sm"
                style={{
                  background: 'rgba(255, 77, 106, 0.08)',
                  color: 'var(--red)',
                  border: '1px solid rgba(255, 77, 106, 0.2)',
                }}
              >
                {error}
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 mt-1"
              style={{
                background: isLoading ? 'var(--gold-dark)' : 'var(--gold)',
                color: '#0A0F1E',
                opacity: isLoading ? 0.8 : 1,
                cursor: isLoading ? 'not-allowed' : 'pointer',
              }}
              onMouseEnter={e => {
                if (!isLoading) e.currentTarget.style.background = 'var(--gold-light)'
              }}
              onMouseLeave={e => {
                if (!isLoading) e.currentTarget.style.background = 'var(--gold)'
              }}
            >
              {isLoading
                ? 'Please wait...'
                : mode === 'login' ? 'Sign in' : 'Create account'
              }
            </button>
          </form>

          {/* Footer toggle */}
          <p className="text-center text-xs mt-5" style={{ color: 'var(--text-muted)' }}>
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
              className="font-medium transition-all"
              style={{ color: 'var(--gold)' }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--gold-light)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--gold)'}
            >
              {mode === 'login' ? 'Create one' : 'Sign in'}
            </button>
          </p>
        </div>

        {/* Demo credentials */}
        <div
          className="mt-4 px-4 py-3 rounded-xl text-xs text-center border"
          style={{
            background: 'rgba(245,200,66,0.04)',
            borderColor: 'rgba(245,200,66,0.12)',
            color: 'var(--text-muted)',
          }}
        >
          Demo: <span style={{ color: 'var(--text-secondary)' }}>test@aurumcap.com</span>
          {' / '}
          <span style={{ color: 'var(--text-secondary)' }}>aurumcap123</span>
        </div>

      </div>
    </div>
  )
}