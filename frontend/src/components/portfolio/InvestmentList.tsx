// components/portfolio/InvestmentList.tsx
import { useState } from "react";
import { FaFilter, FaEdit, FaTrash, FaArrowUp, FaArrowDown } from "react-icons/fa";

interface InvestmentListProps {
  investments: any[];
  onEdit: (investment: any) => void;
  onDelete: (investment: any) => void;
  formatMoney: (n: number) => string;
}

// Tipos de activos disponibles para filtrar
const assetTypeFilters = [
  { value: "all", label: "Todos los activos", color: "bg-gray-500" },
  { value: "stock", label: "Acciones", color: "bg-green-500" },
  { value: "crypto", label: "Cripto", color: "bg-purple-500" },
  { value: "bond", label: "Renta Fija", color: "bg-blue-500" },
  { value: "real_estate", label: "Inmuebles", color: "bg-red-500" },
  { value: "commodity", label: "Commodities", color: "bg-yellow-500" },
  { value: "cash", label: "Efectivo", color: "bg-gray-400" },
  { value: "otros", label: "Otros", color: "bg-indigo-500" },
];

// Función para obtener color basado en el tipo de activo
const getColorForAssetType = (type: string) => {
  const colorMap: { [key: string]: string } = {
    stock: "#10B981", // green-500
    crypto: "#8B5CF6", // purple-500
    bond: "#3B82F6", // blue-500
    real_estate: "#EF4444", // red-500
    commodity: "#F59E0B", // yellow-500
    cash: "#6B7280", // gray-500
    otros: "#6366F1", // indigo-500
  };
  return colorMap[type.toLowerCase()] || "#9CA3AF";
};

// Función para formatear el nombre del tipo de activo
const formatAssetTypeName = (type: string) => {
  const nameMap: { [key: string]: string } = {
    stock: "Acciones",
    crypto: "Cripto",
    bond: "Renta Fija",
    real_estate: "Inmuebles",
    commodity: "Commodities",
    cash: "Efectivo",
    otros: "Otros",
  };
  return nameMap[type.toLowerCase()] || type;
};

export default function InvestmentList({ 
  investments, 
  onEdit, 
  onDelete, 
  formatMoney 
}: InvestmentListProps) {
  const [assetFilter, setAssetFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"name" | "value" | "roi">("value");

  // Filtrar y ordenar inversiones
  const filteredAndSortedInvestments = investments
    .filter(inv => assetFilter === "all" || inv.asset_type === assetFilter)
    .sort((a, b) => {
      switch (sortBy) {
        case "name":
          return (a.asset_name || a.symbol).localeCompare(b.asset_name || b.symbol);
        case "roi":
          return (b.roi || 0) - (a.roi || 0);
        case "value":
        default:
          return (b.current_value || 0) - (a.current_value || 0);
      }
    });

  // Obtener tipos de activos únicos de las inversiones
  const availableAssetTypes = Array.from(
    new Set(investments.map(inv => inv.asset_type || "otros"))
  );

  return (
    <section className="bg-white rounded-2xl shadow-sm p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900">Lista de Inversiones</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            {filteredAndSortedInvestments.length} activos
            {assetFilter !== "all" && ` de ${formatAssetTypeName(assetFilter)}`}
          </span>
        </div>
      </div>

      {/* Filtros y Ordenamiento */}
      <div className="mb-6 space-y-4">
        {/* Filtro por tipo de activo */}
        <div>
          <div className="flex items-center gap-3 mb-3">
            <FaFilter className="text-gray-400" size={16} />
            <span className="text-sm font-medium text-gray-700">Filtrar por tipo:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {assetTypeFilters
              .filter((filter) => {
                if (filter.value === "all") return true;
                return availableAssetTypes.includes(filter.value);
              })
              .map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setAssetFilter(filter.value)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    assetFilter === filter.value
                      ? "bg-[#B59F50] text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full ${filter.color}`} />
                  {filter.label}
                </button>
              ))}
          </div>
        </div>

        {/* Ordenamiento */}
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-sm font-medium text-gray-700">Ordenar por:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              { value: "value", label: "Valor" },
              { value: "roi", label: "ROI" },
              { value: "name", label: "Nombre" },
            ].map((sort) => (
              <button
                key={sort.value}
                onClick={() => setSortBy(sort.value as any)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  sortBy === sort.value
                    ? "bg-[#B59F50] text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {sort.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Grid de Tarjetas de Activos */}
      {filteredAndSortedInvestments.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAndSortedInvestments.map((investment) => {
            const currentValue = investment.current_value || 0;
            const gain = investment.gain || 0;
            const roi = investment.roi || 0;
            const isPositive = roi >= 0;

            return (
              <div
                key={investment.id}
                className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-all duration-300 hover:border-gray-300"
              >
                {/* Header de la tarjeta */}
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
                      style={{ 
                        backgroundColor: getColorForAssetType(investment.asset_type || 'otros') 
                      }}
                    >
                      {investment.symbol?.charAt(0) || investment.asset_name?.charAt(0) || 'A'}
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900 text-sm">
                        {investment.asset_name || investment.symbol}
                      </h3>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 font-mono text-xs">
                          {investment.symbol}
                        </span>
                        <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                          {formatAssetTypeName(investment.asset_type || 'otros')}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Indicador de rendimiento */}
                  <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                    isPositive ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                  }`}>
                    {isPositive ? <FaArrowUp size={10} /> : <FaArrowDown size={10} />}
                    {isPositive ? '+' : ''}{roi.toFixed(2)}%
                  </div>
                </div>

                {/* Valor principal */}
                <div className="mb-3">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatMoney(currentValue)}
                  </div>
                  {gain !== 0 && (
                    <div className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {isPositive ? '+' : ''}{formatMoney(gain)}
                    </div>
                  )}
                </div>

                {/* Detalles adicionales */}
                <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <div className="text-gray-500 text-xs">Cantidad</div>
                    <div className="font-semibold text-gray-900">
                      {investment.quantity || 'N/A'}
                    </div>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <div className="text-gray-500 text-xs">Plataforma</div>
                    <div className="font-semibold text-gray-900 truncate">
                      {investment.platform || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Botones de acción */}
                <div className="flex gap-2">
                  <button
                    onClick={() => onEdit(investment)}
                    className="flex-1 py-2 text-sm bg-[#B59F50] text-white rounded-lg hover:bg-[#A68F45] transition-colors font-medium flex items-center justify-center gap-2"
                  >
                    <FaEdit size={12} />
                    Editar
                  </button>
                  <button
                    onClick={() => onDelete(investment)}
                    className="flex-1 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium flex items-center justify-center gap-2"
                  >
                    <FaTrash size={12} />
                    Eliminar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          {assetFilter === "all" ? (
            <>
              <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
                <span className="text-gray-400 text-2xl">💼</span>
              </div>
              <p className="text-gray-500 mb-2">No hay inversiones registradas</p>
              <p className="text-gray-400 text-sm">
                Comienza agregando tu primera inversión
              </p>
            </>
          ) : (
            <>
              <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
                <FaFilter className="text-gray-400" size={24} />
              </div>
              <p className="text-gray-500 mb-2">
                No hay inversiones de {formatAssetTypeName(assetFilter)}
              </p>
              <button
                onClick={() => setAssetFilter("all")}
                className="px-6 py-3 bg-[#B59F50] text-white font-semibold rounded-lg hover:bg-[#A68F45] transition-colors"
              >
                Ver todos los activos
              </button>
            </>
          )}
        </div>
      )}
    </section>
  );
}