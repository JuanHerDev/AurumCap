"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

import {
  loginRequest,
  registerRequest,
  logoutRequest,
  meRequest,
} from "@/features/auth/services/auth.service";

import { changePasswordRequest, updateUserRequest } from "@/features/auth/services/auth.service";

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
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  updateUser: (userData: { full_name?: string, picture_url?: string}) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();


  async function bootstrap() {
    setLoading(true);

    try {
      const token = getAccessToken();

      if (token) {
        const userData = await meRequest();
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.warn("Bootstrap failed:", error);
      setUser(null);
      setAccessToken(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bootstrap();
  }, []);


  const login = async (email: string, password: string) => {
    const res = await loginRequest(email, password);

    if (res?.access_token) setAccessToken(res.access_token);

    await refreshUser();
    router.push("/dashboard");
  };


  const register = async (
    email: string,
    password: string,
    name?: string
  ) => {
    const res = await registerRequest(email, password, name);

    if (res?.access_token) setAccessToken(res.access_token);

    await refreshUser();
    router.push("/dashboard");
  };


  const refreshUser = async () => {
    try {
      const data = await meRequest();
      setUser(data);
    } catch (err) {
      console.warn("refreshUser error:", err);
      setUser(null);
      setAccessToken(null);
      throw err;
    }
  };


  const logout = async () => {
    try {
      await logoutRequest();
    } catch (_) {}

    setUser(null);
    setAccessToken(null);
    router.push("/login");
  };

  const changePassword = async (currentPassword: string, newPassword: string) => {
    try {
      await changePasswordRequest({
        current_password: currentPassword,
        new_password: newPassword
      });
    } catch (error) {
      console.error("Error changing password:", error);
      throw error;
    }
  };

  const updateUser = async (userData: { full_name?: string, picture_url?: string }) => {
    try {
      const updatedUser = await updateUserRequest(userData);
      setUser(updatedUser);
    } catch (error) {
      console.error("Error updating user:", error);
      throw error;
    }
  };


  const protectedRoutes = ["/dashboard", "/profile", "/investments"];
  const isProtected = protectedRoutes.some((r) => pathname.startsWith(r));

  useEffect(() => {
    if (!loading && isProtected && !user) {
      router.push("/login");
    }
  }, [loading, user, pathname]);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refreshUser, changePassword, updateUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
