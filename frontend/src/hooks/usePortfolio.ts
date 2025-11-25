// src/hooks/usePortfolio.ts
"use client";

import { useEffect, useState, useCallback } from "react";
import * as service from "@/features/portfolio/services/portfolio.service";
import { AuthService } from "@/services/auth.service";

export interface UsePortfolioResult {
  summary: any | null;
  investments: any[];
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  create: (payload: any) => Promise<any>;
  update: (id: number, payload: any) => Promise<any>;
  remove: (id: number) => Promise<void>;
}

export function usePortfolio(): UsePortfolioResult {
  const [summary, setSummary] = useState<any | null>(null);
  const [investments, setInvestments] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  // Verificar autenticación antes de hacer requests
  const checkAuth = useCallback(() => {
    const token = AuthService.getToken();
    if (!token || !AuthService.isValidToken(token)) {
      throw new Error('Authentication required. Please login again.');
    }
    return token;
  }, []);

  // Charge backend data
  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      checkAuth(); // Verificar autenticación primero
      
      const [s, list] = await Promise.all([
        service.getSummary(),
        service.getInvestments(),
      ]);

      setSummary(s ?? null);
      setInvestments(list ?? []);
    } catch (err: any) {
      console.error('❌ Error fetching portfolio data:', err);
      
      // Manejar específicamente errores de autenticación
      if (err.status === 401 || err.message.includes('Authentication')) {
        AuthService.removeToken();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
      
      setError(err);
    }
  }, [checkAuth]);

  // Charge initial data
  useEffect(() => {
    fetchAll().finally(() => setLoading(false));
  }, [fetchAll]);

  // Refresh data manually
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      await fetchAll();
    } finally {
      setLoading(false);
    }
  }, [fetchAll]);

  // Create new investment
  const create = useCallback(
    async (payload: any) => {
      setLoading(true);
      try {
        checkAuth(); // Verificar autenticación primero
        
        const created = await service.createInvestment(payload);

        // Refresh data after creation
        await fetchAll();
        return created;
      } catch (err: any) {
        console.error('❌ Error creating investment:', err);
        
        // Manejar específicamente errores de autenticación
        if (err.status === 401 || err.message.includes('Authentication')) {
          AuthService.removeToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchAll, checkAuth]
  );

  // Actualizate existing investment
  const update = useCallback(
    async (id: number, payload: any) => {
      setLoading(true);
      try {
        checkAuth(); // Verificar autenticación primero
        
        const updated = await service.updateInvestment(id, payload);
        await fetchAll();
        return updated;
      } catch (err: any) {
        console.error('❌ Error updating investment:', err);
        
        // Manejar específicamente errores de autenticación
        if (err.status === 401 || err.message.includes('Authentication')) {
          AuthService.removeToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchAll, checkAuth]
  );

  // Delete investment
  const remove = useCallback(
    async (id: number) => {
      setLoading(true);
      try {
        checkAuth(); // Verificar autenticación primero
        
        await service.deleteInvestment(id);
        await fetchAll();
      } catch (err: any) {
        console.error('❌ Error deleting investment:', err);
        
        // Manejar específicamente errores de autenticación
        if (err.status === 401 || err.message.includes('Authentication')) {
          AuthService.removeToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchAll, checkAuth]
  );

  return {
    summary,
    investments,
    loading,
    error,
    refresh,
    create,
    update,
    remove,
  };
}