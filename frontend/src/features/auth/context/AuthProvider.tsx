"use client";
import React, { createContext, useContext, useEffect, useState } from "react";
import { loginRequest, registerRequest, logoutRequest, meRequest } from "@/features/auth/services/auth.service";
import { useRouter } from "next/navigation";

type User = {
    id: number;
    email: string;
    full_name?: string;
    role?: string;
};

type AuthContextType = {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name?: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser ] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    // On mount | Try to fetch /auth/me
    async function bootstrap() {
        setLoading(true);
        try {
            const data = await meRequest();
            setUser(data);
        } catch (e) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        bootstrap();
    }, []);

    const login = async (email: string, password: string) => {
        await loginRequest(email, password);

        // After Login token stored, fetch user
        await refreshUser();
        router.push("/dashboard");
    };

    const register = async (email: string, password: string, name?: string) => {
        await registerRequest(email, password, name);
        await refreshUser();
        router.push("/dashboard");
    };

    const logout = async () => {
        try {
            await logoutRequest();
        } finally {
            setUser(null);
            router.push("/login");
        }
    };

    const refreshUser = async () => {
        try {
            const data = await meRequest();
            setUser(data);
        } catch (e) {
            setUser(null);
            throw e;
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
}


export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be inside AuthProvider");
    return ctx;
}