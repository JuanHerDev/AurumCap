// components/portfolio/PortfolioHeader.tsx
import { FaSyncAlt, FaBriefcase } from "react-icons/fa";

interface PortfolioHeaderProps {
  portfolioMetrics: any;
  onRefresh: () => void;
  loading: boolean;
  formatMoney: (n: number) => string;
}

export default function PortfolioHeader({ 
  portfolioMetrics, 
  onRefresh, 
  loading, 
  formatMoney 
}: PortfolioHeaderProps) {
  return (
    <header className="bg-white px-6 py-4 border-b border-gray-200">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <FaBriefcase className="text-[#B59F50]" size={24} />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Portafolio</h1>
            <p className="text-gray-500 text-sm">Visión unificada de tus inversiones</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          {/* Métricas del Portafolio */}
          {portfolioMetrics && (
            <div className="text-right">
              <p className="text-sm text-gray-500">Valor Total</p>
              <p className="text-2xl font-bold text-[#B59F50]">
                {formatMoney(portfolioMetrics.totalCurrentValue || 0)}
              </p>
              {portfolioMetrics.totalGainLoss !== undefined && (
                <p className={`text-sm ${
                  portfolioMetrics.totalGainLoss >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  {portfolioMetrics.totalGainLoss >= 0 ? '+' : ''}
                  {formatMoney(portfolioMetrics.totalGainLoss)} • 
                  {portfolioMetrics.totalROI >= 0 ? '+' : ''}
                  {portfolioMetrics.totalROI?.toFixed(2)}%
                </p>
              )}
            </div>
          )}
          
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={loading}
          >
            <FaSyncAlt size={16} className={loading ? "animate-spin" : ""} />
            <span className="text-sm font-medium">
              {loading ? "Actualizando..." : "Actualizar"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}