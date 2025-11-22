import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL,
  withCredentials: true, // send cookies (refresh token)
  headers: {
    "Content-Type": "application/json",
  },
});

export const TOKEN_KEY = "aurum_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (!token) localStorage.removeItem(TOKEN_KEY);
  else localStorage.setItem(TOKEN_KEY, token);
}


// Request interceptor
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    // Ensure headers object exists and set Authorization in a type-safe way
    if (!config.headers) {
      config.headers = {} as any;
    }
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
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

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    if (!originalRequest) return Promise.reject(error);
    if (error.response?.status !== 401) return Promise.reject(error);
    if (originalRequest._retry) return Promise.reject(error);

    originalRequest._retry = true;


    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((newToken) => {
        if (newToken)
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      });
    }


    isRefreshing = true;

    try {
      const refreshResponse = await axios.post(
        `${baseURL}/auth/refresh`,
        {},
        { withCredentials: true }
      );

      const newToken = refreshResponse.data?.access_token;
      if (!newToken) throw new Error("No access_token returned from refresh");

      setAccessToken(newToken);

      processQueue(null, newToken);


      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      setAccessToken(null); 
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
