"use client";

import { useEffect, useState, useCallback } from "react";
import * as service from "@/features/portfolio/services/portfolio.service";

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

  // Charge backend data
  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [s, list] = await Promise.all([
        service.getSummary(),
        service.getInvestments(),
      ]);

      setSummary(s ?? null);
      setInvestments(list ?? []);
    } catch (err: any) {
      setError(err);
    }
  }, []);

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
        const created = await service.createInvestment(payload);

        // Refresh data after creation
        await fetchAll();
        return created;
      } catch (err: any) {
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchAll]
  );

  // Actualizate existing investment
  const update = useCallback(
    async (id: number, payload: any) => {
      setLoading(true);
      try {
        const updated = await service.updateInvestment(id, payload);
        await fetchAll();
        return updated;
      } catch (err: any) {
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchAll]
  );

  // Delete investment
  const remove = useCallback(
    async (id: number) => {
      setLoading(true);
      try {
        await service.deleteInvestment(id);
        await fetchAll();
      } catch (err: any) {
        setError(err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchAll]
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
