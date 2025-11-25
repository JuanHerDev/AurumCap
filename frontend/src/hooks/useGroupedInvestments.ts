// hooks/useGroupedInvestments.ts
import { useMemo } from 'react';

export interface Investment {
  id: number;
  symbol: string;
  asset_name: string;
  asset_type: 'crypto' | 'stock' | 'etf' | 'other';
  quantity: number;
  invested_amount: number;
  purchase_price: number;
  currency: string;
  platform_id?: number;
  created_at: string;
  current_price?: number;
  current_value?: number;
  gain?: number;
  roi?: number;
  notes?: string;
}

export interface GroupedInvestment {
  symbol: string;
  asset_name: string;
  asset_type: string;
  total_quantity: number;
  total_invested: number;
  average_price: number;
  current_price: number;
  current_value: number;
  total_gain: number;
  total_roi: number;
  currency: string;
  entries: Investment[];
  entry_count: number;
  first_investment: string;
  last_investment: string;
  platform_id?: number;
}

export function useGroupedInvestments(investments: Investment[]): GroupedInvestment[] {
  return useMemo(() => {
    if (!investments?.length) return [];

    const groups: { [symbol: string]: GroupedInvestment } = {};

    investments.forEach(investment => {
      const symbol = investment.symbol;
      
      if (!groups[symbol]) {
        groups[symbol] = {
          symbol,
          asset_name: investment.asset_name,
          asset_type: investment.asset_type,
          total_quantity: 0,
          total_invested: 0,
          average_price: 0,
          current_price: investment.current_price || investment.purchase_price,
          current_value: 0,
          total_gain: 0,
          total_roi: 0,
          currency: investment.currency,
          entries: [],
          entry_count: 0,
          first_investment: investment.created_at,
          last_investment: investment.created_at,
          platform_id: investment.platform_id
        };
      }

      const group = groups[symbol];
      
      // Acumular valores
      group.total_quantity += investment.quantity;
      group.total_invested += investment.invested_amount;
      group.entries.push(investment);
      group.entry_count++;
      
      // Actualizar fechas
      if (new Date(investment.created_at) < new Date(group.first_investment)) {
        group.first_investment = investment.created_at;
      }
      if (new Date(investment.created_at) > new Date(group.last_investment)) {
        group.last_investment = investment.created_at;
      }
    });

    // Calcular métricas finales
    Object.values(groups).forEach(group => {
      group.average_price = group.total_invested / group.total_quantity;
      
      // Usar el precio más reciente de las entradas
      const latestEntry = group.entries.reduce((latest, entry) => 
        new Date(entry.created_at) > new Date(latest.created_at) ? entry : latest
      );
      group.current_price = latestEntry.current_price || latestEntry.purchase_price;
      group.current_value = group.total_quantity * group.current_price;
      group.total_gain = group.current_value - group.total_invested;
      group.total_roi = (group.total_gain / group.total_invested) * 100;
    });

    return Object.values(groups).sort((a, b) => b.total_invested - a.total_invested);
  }, [investments]);
}