// src/components/AuthChecker.tsx
'use client';
import { useEffect } from 'react';
import { AuthService } from '../services/auth.service';

export const AuthChecker = () => {
  useEffect(() => {
    const checkAuth = () => {
      const token = AuthService.getToken();
      if (!token || !AuthService.isValidToken(token)) {
        console.log('🔐 No valid token found, redirecting to login...');
        AuthService.removeToken();
        // Usar replace en lugar de href para evitar guardar en historial
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.replace('/login');
        }
      }
    };

    checkAuth();
    
    // Verificar periódicamente (cada 5 minutos)
    const interval = setInterval(checkAuth, 300000);
    
    return () => clearInterval(interval);
  }, []);

  return null;
};