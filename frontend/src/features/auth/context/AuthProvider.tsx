"use client";
import React, { createContext, useContext, useEffect, useState } from "react";
import { loginRequest, registerRequest, logoutRequest, meRequest } from "@/features/auth/services/auth.service";
import { useRouter } from "next/navigation";
import { setAccessToken, getAccessToken } from "@/lib/api";

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
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Inicializar sesión
  async function bootstrap() {
    setLoading(true);
    try {
      const token = getAccessToken();
      if (token) {
        const data = await meRequest();
        setUser(data);
      } else {
        setUser(null);
      }
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
    try {
      const res = await loginRequest(email, password);
      const token = res.access_token;
      if (token) setAccessToken(token);

      await refreshUser();
      router.push("/dashboard");
    } catch (err) {
      throw err;
    }
  };

  const register = async (email: string, password: string, name?: string) => {
    const res = await registerRequest(email, password, name);
    const token = res.access_token;
    if (token) setAccessToken(token);

    await refreshUser();
    router.push("/dashboard");
  };

  const logout = async () => {
    try {
      await logoutRequest();
    } finally {
      setAccessToken(null);
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
      setAccessToken(null);
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
