import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from "@/lib/api";

interface User {
    id: number;
    email: string;
    name?: string;
}

interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;

    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            loading: false,
            error: null,

            // LOGIN ACTION
            login: async (email: string, password: string) => {
                try {
                    set({ loading: true, error: null });
                    const res = await api.post("/auth/login", { email, password });

                    const { access_token, refresh_token, user } = res.data;

                    localStorage.setItem("access_token", access_token);
                    localStorage.setItem("refresh_token", refresh_token);

                    set({
                        user,
                        accessToken: access_token,
                        refreshToken: refresh_token,
                        isAuthenticated: true,
                    });
                } catch (err:any) {
                    console.error("Login error:", err);
                    set({ error: "Credentials are incorrect or server error." });
                    throw err;
                } finally {
                    set({ loading: false });
                }
            },

            // LOGOUT ACTION
            logout: () => {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                    error: null,
                });
            },

            // CHECK AUTH ACTION
            checkAuth: async () => {
                const token = localStorage.getItem("access_token");
                if (!token) {
                    set({ isAuthenticated: false });
                    return;
                }

                try {
                    const res = await api.get("/auth/me");
                    set({
                        user: res.data,
                        isAuthenticated: true,
                    });
                } catch (err) {
                    console.warn("Invalid or expired token, logout session. ");
                    get().logout();
                }
            },
        }),
        {
            name: "auth-storage",
            partialize: (state) => ({
                user: state.user,
                accessToken: state.accessToken,
                refreshToken: state.refreshToken,
                isAuthenticated: state.isAuthenticated,
            }),
        }      
    )
);