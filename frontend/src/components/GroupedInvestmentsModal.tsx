// components/GroupedInvestmentsModal.tsx
'use client';

import React, { useState } from 'react';
import { GroupedInvestment, useGroupedInvestments, type Investment } from '@/hooks/useGroupedInvestments';
import { InvestmentDetailsModal } from './InvestmentDetailsModal';

interface GroupedInvestmentsModalProps {
  investments: any[];
}

export function GroupedInvestmentsModal({ investments }: GroupedInvestmentsModalProps) {
  const [selectedGroup, setSelectedGroup] = useState<GroupedInvestment | null>(null);
  const groupedInvestments = useGroupedInvestments(investments);

  const formatCurrency = (amount: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatPercentage = (value: number): string => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (!groupedInvestments.length) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 text-lg">No hay inversiones para mostrar</div>
        <p className="text-gray-400 mt-2">Comienza agregando tu primera inversión</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {groupedInvestments.map(group => (
          <div 
            key={group.symbol} 
            className="border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer"
            onClick={() => setSelectedGroup(group)}
          >
            <div className="p-6">
              <div className="flex justify-between items-start">
                {/* Información principal */}
                <div className="flex items-start space-x-4 flex-1">
                  {/* Icono de estado */}
                  <div className={`w-4 h-4 rounded-full mt-2 flex-shrink-0 ${
                    group.total_gain >= 0 ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-bold text-xl text-gray-900 truncate">
                        {group.symbol}
                      </h3>
                      <span className={`text-xs px-2 py-1 rounded-full capitalize ${
                        group.asset_type === 'crypto' 
                          ? 'bg-purple-100 text-purple-800' 
                          : group.asset_type === 'stock'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {group.asset_type}
                      </span>
                    </div>
                    
                    <p className="text-gray-600 text-sm truncate mb-3">
                      {group.asset_name}
                    </p>
                    
                    {/* Métricas rápidas */}
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <span className="font-medium">{group.entry_count}</span>
                        <span>entr{group.entry_count === 1 ? 'y' : 'ies'}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span>Promedio:</span>
                        <span className="font-medium">{formatCurrency(group.average_price, group.currency)}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span>Cantidad:</span>
                        <span className="font-medium">{group.total_quantity.toFixed(4)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Valores y indicador */}
                <div className="text-right ml-4">
                  <div className="font-bold text-2xl text-gray-900 mb-1">
                    {formatCurrency(group.current_value, group.currency)}
                  </div>
                  <div className={`text-lg font-semibold ${
                    group.total_gain >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(group.total_gain, group.currency)} 
                    <span className="text-sm font-normal ml-2">
                      ({formatPercentage(group.total_roi)})
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Invertido: {formatCurrency(group.total_invested, group.currency)}
                  </div>
                </div>
              </div>

              {/* Barra de progreso visual */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Invertido</span>
                  <span>Valor actual</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-500 ${
                      group.total_gain >= 0 ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    style={{ 
                      width: `${Math.min(100, (group.current_value / group.total_invested) * 100)}%` 
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal de detalles */}
      {selectedGroup && (
        <InvestmentDetailsModal
          group={selectedGroup}
          onClose={() => setSelectedGroup(null)}
        />
      )}
    </>
  );
}