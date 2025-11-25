// src/services/api.interceptor.ts
import { AuthService } from './auth.service';

export class ApiInterceptor {
  static async fetchWithAuth(
    url: string, 
    options: RequestInit = {}
  ): Promise<Response> {
    console.log(`🔐 ApiInterceptor: Making request to ${url}`);
    
    let token = AuthService.getToken();
    
    // Verificar si el token es válido
    if (token && AuthService.isTokenExpired(token)) {
      console.log('🔄 Token expirado, intentando refresh...');
      token = await AuthService.refreshToken();
    }

    if (!token || !AuthService.isValidToken(token)) {
      console.error('❌ No hay token válido disponible');
      AuthService.removeToken();
      // Redirigir al login si es necesario
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        console.log('🔐 Redirigiendo a login...');
        window.location.href = '/login';
      }
      throw new Error('Authentication required');
    }

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    console.log(`🔐 Headers con token:`, { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token.substring(0, 20)}...` 
    });

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      });

      console.log(`🔐 Response status: ${response.status} for ${url}`);

      // Manejar error de autenticación
      if (response.status === 401) {
        console.log('🔐 Token inválido (401), limpiando y redirigiendo...');
        AuthService.removeToken();
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        throw new Error('Authentication failed');
      }

      return response;
    } catch (error) {
      console.error('❌ Error en fetchWithAuth:', error);
      throw error;
    }
  }
}