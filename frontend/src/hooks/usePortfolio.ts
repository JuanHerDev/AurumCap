import { useEffect, useState, useCallback } from "react";
import * as service from "@/features/portfolio/services/portfolio.service";

export function usePortfolio(pollIntervalMs?: number) {
  const [summary, setSummary] = useState<any | null>(null);
  const [investments, setInvestments] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, list] = await Promise.all([service.getSummary(), service.getInvestments()]);
      setSummary(s ?? null);
      setInvestments(list ?? []);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    let intervalId: any;
    if (pollIntervalMs) {
      intervalId = setInterval(fetchAll, pollIntervalMs);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchAll, pollIntervalMs]);

  const refresh = useCallback(() => {
    fetchAll();
  }, [fetchAll]);

  const create = useCallback(async (payload: any) => {
    setLoading(true);
    try {
      const created = await service.createInvestment(payload);
      // optimistic refresh: push then refetch summary
      await fetchAll();
      return created;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchAll]);

  const update = useCallback(async (id: number, payload: any) => {
    setLoading(true);
    try {
      const updated = await service.updateInvestment(id, payload);
      await fetchAll();
      return updated;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchAll]);

  const remove = useCallback(async (id: number) => {
    setLoading(true);
    try {
      await service.deleteInvestment(id);
      await fetchAll();
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchAll]);

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
