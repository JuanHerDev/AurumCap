import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// Shared interceptors — reused across both clients
const attachToken = (config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}

const handleAuthError = (error) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/auth'
  }
  return Promise.reject(error)
}

// Standard client — 60s timeout for most endpoints
const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})
client.interceptors.request.use(attachToken)
client.interceptors.response.use(r => r, handleAuthError)

// Analytics client — 5 min timeout for rate-limited historical data
// TwelveData free plan (8 credits/min) causes the backend to queue requests,
// which can take 2-3 minutes to complete for a 6-holding portfolio
export const analyticsClient = axios.create({
  baseURL: BASE_URL,
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
})
analyticsClient.interceptors.request.use(attachToken)
analyticsClient.interceptors.response.use(r => r, handleAuthError)

export default client