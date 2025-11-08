import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
    baseURL,
    withCredentials: true, // Send refresh cookio on /auth/refresh
    headers: {
        "Content-Type": "application/json",
    },
});

// Helper to read token from sessionStorage
export function getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem("aurum_access_token");
}

export function setAccessToken(token: string | null) {
    if (typeof window === "undefined") return;
    if (!token) sessionStorage.removeItem("aurum_access_token");
    else sessionStorage.setItem("aurum_access_token", token);
}

// Attach access token before requests
api.interceptors.request.use((cfg) => {
  const token = getAccessToken();
  if (token) cfg.headers = { ...(cfg.headers as any), Authorization: `Bearer ${token}` };
  return cfg;
});

// Response interceptor: try refresh on 401 once and retry request
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (err?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((p) => {
        if (error) p.reject(error);
        else p.resolve(token);
    });
    failedQueue = [];
}

api.interceptors.response.use(
    (res) => res,
    async (err) => {
        const originalRequest = err.config;
        if (!originalRequest) return Promise.reject(err);

        // Ignore if no response or not 401
        if (err.response?.status !== 401) return Promise.reject(err);

        // Prevent infinite loop
        if (originalRequest._retry) return Promise.reject(err);
        originalRequest._retry = true;

        if (isRefreshing) {
            return new Promise(function (resolve, reject) {
                failedQueue.push({ resolve, reject });
            })
            .then((token) => {
                if (token) originalRequest.headers.Authorization = `Bearer ${token}`;
                return api(originalRequest);
            })
            .catch((e) => Promise.reject(e));
        }

        isRefreshing = true;

        try {
            // Call refresh endpoint to set a new access_token
            const refreshRes = await api.post("/auth/refresh");
            const newToken = refreshRes.data?.access_token;

            if (newToken) {
                setAccessToken(newToken);
                processQueue(null, newToken);
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return api(originalRequest);
            } else {
                // No token returned | Logout
                processQueue(new Error("No token"), null);
                return Promise.reject(err);
            }
        } catch (refreshErr) {
            processQueue(refreshErr, null);
            return Promise.reject(refreshErr);
        } finally {
            isRefreshing = false;
        }
    }
);

export default api;