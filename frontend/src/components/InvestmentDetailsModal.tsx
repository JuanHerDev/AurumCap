// components/InvestmentDetailsModal.tsx
'use client';

import React from 'react';
import { type GroupedInvestment } from '@/hooks/useGroupedInvestments';

interface InvestmentDetailsModalProps {
  group: GroupedInvestment;
  onClose: () => void;
}

export function InvestmentDetailsModal({ group, onClose }: InvestmentDetailsModalProps) {
  const formatCurrency = (amount: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Prevenir que el click en el modal cierre el overlay
  const handleModalClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-scaleIn"
        onClick={handleModalClick}
      >
        {/* Header del modal */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-4">
              <div className={`w-4 h-4 rounded-full ${
                group.total_gain >= 0 ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {group.symbol} - {group.asset_name}
                </h2>
                <p className="text-gray-600 mt-1 capitalize">
                  {group.asset_type} • {group.entry_count} entr{group.entry_count === 1 ? 'y' : 'ies'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl w-8 h-8 flex items-center justify-center hover:bg-gray-100 rounded-full transition-colors"
            >
              ×
            </button>
          </div>
        </div>

        {/* Contenido del modal */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Métricas principales */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-linear-to-br from-blue-50 to-blue-100 p-5 rounded-xl border border-blue-200">
              <div className="text-blue-700 text-sm font-medium mb-1">Valor actual</div>
              <div className="text-2xl font-bold text-blue-900">
                {formatCurrency(group.current_value, group.currency)}
              </div>
            </div>
            
            <div className="bg-linear-to-br from-gray-50 to-gray-100 p-5 rounded-xl border border-gray-200">
              <div className="text-gray-700 text-sm font-medium mb-1">Total invertido</div>
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(group.total_invested, group.currency)}
              </div>
            </div>
            
            <div className={`p-5 rounded-xl border ${
              group.total_gain >= 0 
                ? 'bg-linear-to-br from-green-50 to-green-100 border-green-200' 
                : 'bg-linear-to-br from-red-50 to-red-100 border-red-200'
            }`}>
              <div className={`text-sm font-medium mb-1 ${
                group.total_gain >= 0 ? 'text-green-700' : 'text-red-700'
              }`}>
                Ganancia/Pérdida
              </div>
              <div className={`text-2xl font-bold ${
                group.total_gain >= 0 ? 'text-green-900' : 'text-red-900'
              }`}>
                {formatCurrency(group.total_gain, group.currency)}
                <span className="text-lg ml-2">
                  ({group.total_roi >= 0 ? '+' : ''}{group.total_roi.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Lista detallada de entradas */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Historial de entradas</h3>
            <div className="space-y-3">
              {group.entries
                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                .map((entry, index) => (
                <div 
                  key={entry.id} 
                  className="flex justify-between items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="w-10 h-10 bg-linear-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                      #{group.entries.length - index}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-gray-900 text-lg">
                        {formatCurrency(entry.invested_amount, entry.currency)}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">
                        {formatDate(entry.created_at)}
                      </div>
                      {entry.notes && (
                        <div className="text-xs text-gray-400 mt-1 italic">
                          {entry.notes}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm text-gray-600 mb-1">
                      {entry.quantity.toFixed(4)} {group.symbol} • {formatCurrency(entry.purchase_price, group.currency)} c/u
                    </div>
                    <div className="font-semibold text-gray-900">
                      Valor: {formatCurrency(
                        (entry.current_price || entry.purchase_price) * entry.quantity, 
                        group.currency
                      )}
                    </div>
                    {entry.gain !== undefined && (
                      <div className={`text-sm ${
                        entry.gain >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {entry.gain >= 0 ? '+' : ''}{formatCurrency(entry.gain, group.currency)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Estadísticas del activo */}
          <div className="bg-linear-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-indigo-900 mb-4">Estadísticas del activo</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-indigo-700 text-sm font-medium mb-1">Precio promedio</div>
                <div className="font-bold text-xl text-indigo-900">
                  {formatCurrency(group.average_price, group.currency)}
                </div>
              </div>
              <div>
                <div className="text-indigo-700 text-sm font-medium mb-1">Cantidad total</div>
                <div className="font-bold text-xl text-indigo-900">
                  {group.total_quantity.toFixed(6)}
                </div>
              </div>
              <div>
                <div className="text-indigo-700 text-sm font-medium mb-1">Primera entrada</div>
                <div className="font-bold text-lg text-indigo-900">
                  {formatDate(group.first_investment)}
                </div>
              </div>
              <div>
                <div className="text-indigo-700 text-sm font-medium mb-1">Última entrada</div>
                <div className="font-bold text-lg text-indigo-900">
                  {formatDate(group.last_investment)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Estilos de animación */}
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { 
            opacity: 0;
            transform: scale(0.9) translateY(-10px);
          }
          to { 
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }
        .animate-scaleIn {
          animation: scaleIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}