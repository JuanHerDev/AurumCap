"use client";

import useSWR from "swr"; // ← IMPORT NOMBRADO
import { getPortfolioSummary } from "@/services/api";
import type { PortfolioSummary } from "@/types/investment";

const fetcher = () => getPortfolioSummary();

export function usePortfolio(pollInterval = 15000) {
  const { data, error, isLoading, mutate } = useSWR(
    "/investments/summary",
    fetcher,
    {
      refreshInterval: pollInterval,
      revalidateOnFocus: true,
    }
  );

  return {
    summary: data,
    isLoading,
    error,
    mutate,
  };
}