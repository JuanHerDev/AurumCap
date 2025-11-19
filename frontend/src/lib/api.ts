import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// -------------------- TOKEN CACHE --------------------
export const TOKEN_KEY = "aurum_access_token";

let memoryToken: string | null = null;

export function getAccessToken(): string | null {
  if (memoryToken) return memoryToken;
  if (typeof window === "undefined") return null;
  memoryToken = sessionStorage.getItem(TOKEN_KEY);
  return memoryToken;
}

export function setAccessToken(token: string | null) {
  memoryToken = token;
  if (typeof window === "undefined") return;
  if (!token) sessionStorage.removeItem(TOKEN_KEY);
  else sessionStorage.setItem(TOKEN_KEY, token);
}

// -------------------- REQUEST INTERCEPTOR --------------------
api.interceptors.request.use((cfg) => {
  const token = getAccessToken();
  if (token) {
    cfg.headers = {
      ...(cfg.headers as any),
      Authorization: `Bearer ${token}`,
    };
  }
  return cfg;
});

// -------------------- REFRESH LOGIC --------------------
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token?: string) => void;
  reject: (err?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token ?? undefined);
  });
  failedQueue = [];
};

// -------------------- RESPONSE INTERCEPTOR --------------------
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config;
    if (!originalRequest) return Promise.reject(err);

    // Only retry once
    if (err.response?.status !== 401 || originalRequest._retry)
      return Promise.reject(err);

    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (token)
          originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      });
    }

    isRefreshing = true;

    try {
      // IMPORTANT: use axios without interceptors
      const refreshRes = await axios.post(
        `${baseURL}/auth/refresh`,
        {},
        { withCredentials: true }
      );

      const newToken = refreshRes.data?.access_token;
      if (!newToken) throw new Error("No refresh token received");

      setAccessToken(newToken);
      processQueue(null, newToken);

      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    } catch (refreshErr) {
      processQueue(refreshErr, null);
      setAccessToken(null);
      return Promise.reject(refreshErr);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
