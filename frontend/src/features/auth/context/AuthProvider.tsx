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
  auth_provider?: string;
  picture_url?: string;
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
  handleGoogleAuth: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isProcessingGoogleAuth, setIsProcessingGoogleAuth] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // Función para iniciar el flujo de Google OAuth
  const handleGoogleAuth = () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      window.location.href = `${apiUrl}/auth/login/google`;
    } catch (err) {
      console.error("Error iniciando sesión con Google:", err);
    }
  };

  // Función para verificar y procesar tokens de Google - USA SESSIONSTORAGE
  const checkForGoogleToken = async (): Promise<boolean> => {
    // ✅ CAMBIAR: Usar sessionStorage en lugar de localStorage
    const token = sessionStorage.getItem('access_token');
    
    if (token) {
      console.log("🔑 Token de Google encontrado en sessionStorage, procesando...");
      setIsProcessingGoogleAuth(true);
      
      try {
        setAccessToken(token);
        await refreshUser();
        // ✅ CAMBIAR: Limpiar de sessionStorage
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('user_email');
        sessionStorage.removeItem('auth_provider');
        console.log("✅ Google auth completado exitosamente");
        return true;
      } catch (error) {
        console.error("❌ Error procesando token de Google:", error);
        // ✅ CAMBIAR: Limpiar de sessionStorage
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('user_email');
        sessionStorage.removeItem('auth_provider');
        setAccessToken(null);
        return false;
      } finally {
        setIsProcessingGoogleAuth(false);
      }
    }
    
    return false;
  };

  async function bootstrap() {
    setLoading(true);

    try {
      // Primero verificar si hay un token de Google
      const hasGoogleToken = await checkForGoogleToken();
      
      // Si no hay token de Google, verificar token normal
      if (!hasGoogleToken) {
        const token = getAccessToken();
        if (token) {
          const userData = await meRequest();
          setUser(userData);
        } else {
          setUser(null);
        }
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

  // Efecto PRINCIPAL para verificar tokens de Google
  useEffect(() => {
    const processGoogleAuth = async () => {
      // Solo procesar si estamos en dashboard y no hay usuario
      if (pathname === '/dashboard' && !user && !loading && !isProcessingGoogleAuth) {
        console.log("🔄 Verificando token de Google en ruta /dashboard...");
        
        const hasGoogleToken = await checkForGoogleToken();
        
        if (!hasGoogleToken && !user && !getAccessToken()) {
          console.log("🚫 No se encontró token válido, redirigiendo a login");
          router.push("/login");
        }
      }
    };

    processGoogleAuth();
  }, [pathname, user, loading, isProcessingGoogleAuth]);

  // Efecto SECUNDARIO para verificar inmediatamente después del callback
  useEffect(() => {
    // ✅ CAMBIAR: Verificar en sessionStorage
    const googleToken = sessionStorage.getItem('access_token');
    if (googleToken && pathname === '/dashboard') {
      console.log("🎯 Token de Google detectado en sessionStorage, procesando inmediatamente...");
      checkForGoogleToken();
    }
  }, [pathname]);

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
      console.log("✅ Usuario actualizado:", data.email);
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
    // ✅ CAMBIAR: Limpiar sessionStorage
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_email');
    sessionStorage.removeItem('auth_provider');
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
    // ✅ CAMBIAR: Verificar sessionStorage
    if (!loading && isProtected && !user && !isProcessingGoogleAuth && !sessionStorage.getItem('access_token')) {
      console.log("🚫 Acceso denegado, redirigiendo a login");
      router.push("/login");
    }
  }, [loading, user, pathname, isProcessingGoogleAuth]);

  // Mostrar loading durante autenticación con Google
  if (isProcessingGoogleAuth) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Completando autenticación con Google...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{ 
        user, 
        loading, 
        login, 
        register, 
        logout, 
        refreshUser, 
        changePassword, 
        updateUser,
        handleGoogleAuth
      }}
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