// src/services/auth.service.ts
export class AuthService {
  static getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('aurum_access_token');
  }

  static setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('aurum_access_token', token);
  }

  static removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('aurum_access_token');
  }

  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000;
      return Date.now() >= exp;
    } catch {
      return true;
    }
  }

  static isValidToken(token: string | null): boolean {
    if (!token) return false;
    return !this.isTokenExpired(token);
  }

  static async refreshToken(): Promise<string | null> {
    try {
      const refreshToken = localStorage.getItem('aurum_refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setToken(data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('aurum_refresh_token', data.refresh_token);
        }
        return data.access_token;
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
    }

    this.removeToken();
    localStorage.removeItem('aurum_refresh_token');
    return null;
  }

  static getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}