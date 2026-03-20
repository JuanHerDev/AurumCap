import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

const client = axios.create({
    baseURL: BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Attach JWT token to every request automatically
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Handle auth errors globally
client.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href='/auth'
        }
        return Promise.reject(error)
    }
)

export default client