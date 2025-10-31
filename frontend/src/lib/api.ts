import axios, { AxiosError, AxiosInstance } from 'axios';
import { jwtDecode } from 'jwt-decode';

// Base URL for the API, configurable via environment variable (in development use Localhost)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_USER || "http://127.0.0.1:8000";

// Keys for storing tokens in localStorage
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

// Function to get the access token
function getAccessToken(): string | null {
    return typeof window !== "undefined" ? localStorage.getItem(ACCESS_TOKEN_KEY) : null;
}

// Function to save tokens
function setAccessToken(token: string) {
    if (typeof window !== "undefined") {
        localStorage.setItem(ACCESS_TOKEN_KEY, token)
    }
}

// Create an Axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
    headers: {
        "Content-Type": "application/json"
    },
});

// Interceptor of requests to add Authorization header
api.interceptors.request.use(
    (config) => {
        const token = getAccessToken();
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Interceptor of responses to manage the token expiration
let isRefreshing = false;
let failedQueue: { resolve: (value?: unknown) => void; reject: (reason?: any) => void}[] = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // If not response or not 401 error, reject
        if (!error.response || error.response.status !== 401) {
            return Promise.reject(error);
        }

        // Avoid infinite loop
        if (originalRequest._retry) {
            return Promise.reject(error);
        }

        // Mark for avoid multiple refresh simultaneously
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({resolve, reject });
            })
            .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return api(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
            if (!refreshToken) throw new Error("No refresh token found");

            // Call a new access token
            const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: refreshToken,
            });

            const newAccessToken = res.data.access_token;
            setAccessToken(newAccessToken);

            api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
            processQueue(null, newAccessToken);
            return api(originalRequest);
        } catch (err) {
            processQueue(err, null);
            // If refresh fails, redirect to login
            if (typeof window !== "undefined") {
                localStorage.removeItem(ACCESS_TOKEN_KEY);
                localStorage.removeItem(REFRESH_TOKEN_KEY);
                window.location.href = "/login";
            }
            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);

export default api;