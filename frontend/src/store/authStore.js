import { create } from 'zustand'
import client from '../api/client'

const useAuthStore = create((set) => ({
    user: null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    isLoading: false,
    error: null,

    login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
            const { data } = await client.post('/auth/login', { email, password })
            localStorage.setItem('token', data.access_token)
            set ({
                token: data.access_token,
                isAuthenticated: true,
                isLoading: false,
            })
            return true
        } catch (err) {
            set ({
                error: err.response?.data?.detail || 'Invalid credentials',
                isLoading: false,
            })
            return false
        }
    },

    register: async (email, password, fullName) => {
        set ({ isLoading: true, error: null})
        try {
            const { data } = await client.post('/aurh/register', {
                email,
                password,
                full_name: fullName,
            })
            localStorage.setItem('token', data.access_token)
            set ({
                token: data.access_token,
                isAuthenticated: true,
                isLoading: false,
            })
            return true
        } catch (err) {
            set ({
                error: err.response?.data?.detail || 'Registration failed',
                isLoading: false,
            })
            return false
        }
    },

    logout: () => {
        localStorage.removeItem('token')
        set ({ user: null, token:null, isAuthenticated: false })
        window.Location.href = '/auth'
    },

    fetchUser: async () => {
        try {
            const { data } = await client.get('/users/me')
            set ({ user: data })
        } catch {
            // Token expired or failed - interceptor handles redirect
        }
    },
    clearError: () => set({ error: null }),
}))

export default useAuthStore