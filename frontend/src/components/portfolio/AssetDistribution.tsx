// components/portfolio/AssetDistribution.tsx
import { useMemo, useState } from "react";
import { FaChevronDown, FaChevronUp } from "react-icons/fa";

interface AssetDistributionProps {
  investments: any[];
  formatMoney: (n: number) => string;
}

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

// Componente para el gráfico de pastel
const PieChart = ({ data }: { data: any[] }) => {
  const totalValue = data.reduce((sum, item) => sum + item.value, 0);
  let accumulatedAngle = 0;

  return (
    <div className="relative w-48 h-48 mx-auto mb-6">
      <svg
        width="192"
        height="192"
        viewBox="0 0 32 32"
        className="transform -rotate-90"
      >
        {data.map((item, index) => {
          const percentage = (item.value / totalValue) * 100;
          const angle = (percentage / 100) * 360;
          const largeArcFlag = angle > 180 ? 1 : 0;

          const x1 = 16 + 16 * Math.cos((accumulatedAngle * Math.PI) / 180);
          const y1 = 16 + 16 * Math.sin((accumulatedAngle * Math.PI) / 180);

          accumulatedAngle += angle;

          const x2 = 16 + 16 * Math.cos((accumulatedAngle * Math.PI) / 180);
          const y2 = 16 + 16 * Math.sin((accumulatedAngle * Math.PI) / 180);

          const pathData = [
            `M 16 16`,
            `L ${x1} ${y1}`,
            `A 16 16 0 ${largeArcFlag} 1 ${x2} ${y2}`,
            `Z`,
          ].join(" ");

          return (
            <path
              key={index}
              d={pathData}
              fill={item.color}
              stroke="#fff"
              strokeWidth="0.5"
            />
          );
        })}
      </svg>

      {/* Centro del gráfico con el total */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">
            {data.length > 0 ? `${data.length}` : '0'}
          </div>
          <div className="text-xs text-gray-500">activos</div>
        </div>
      </div>
    </div>
  );
};

export default function AssetDistribution({ investments, formatMoney }: AssetDistributionProps) {
  const [showAllInvestments, setShowAllInvestments] = useState(false);
  
  const assetDistribution = useMemo(() => {
    if (!investments?.length) return [];

    // Agrupar por tipo de activo y calcular totales
    const assetMap = new Map();

    investments.forEach((investment) => {
      const type = investment.asset_type || "otros";
      const currentValue = investment.current_value || 0;

      if (assetMap.has(type)) {
        const existing = assetMap.get(type);
        assetMap.set(type, {
          ...existing,
          value: existing.value + currentValue,
          count: existing.count + 1,
        });
      } else {
        assetMap.set(type, {
          name: type,
          value: currentValue,
          count: 1,
          color: getColorForAssetType(type),
        });
      }
    });

    // Calcular porcentajes
    const totalValue = Array.from(assetMap.values()).reduce(
      (sum, asset) => sum + asset.value,
      0
    );

    return Array.from(assetMap.values()).map((asset) => ({
      ...asset,
      percentage: totalValue > 0 ? (asset.value / totalValue) * 100 : 0,
      displayName: formatAssetTypeName(asset.name),
    }));
  }, [investments]);

  // Determinar cuántos activos mostrar en la vista previa
  const previewCount = 5;
  const shouldShowToggle = investments.length > previewCount;
  const displayedInvestments = showAllInvestments 
    ? investments 
    : investments.slice(0, previewCount);

  return (
    <section className="space-y-6">
      {/* Distribución de Activos */}
      <div className="bg-white rounded-2xl p-6 shadow-sm">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Distribución de Activos</h2>
        
        {assetDistribution.length > 0 ? (
          <div className="flex flex-col lg:flex-row items-center lg:items-start gap-8">
            {/* Gráfico de pastel */}
            <div className="shrink-0">
              <PieChart data={assetDistribution} />
            </div>

            {/* Leyenda de activos */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              {assetDistribution.map((asset) => (
                <div
                  key={asset.name}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: asset.color }}
                    />
                    <div>
                      <p className="font-medium text-gray-900 text-sm">
                        {asset.displayName}
                      </p>
                      <p className="text-xs text-gray-500">
                        {asset.count} activo{asset.count !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">
                      {asset.percentage.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatMoney(asset.value)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-gray-400 text-2xl">📊</span>
            </div>
            <p className="text-gray-500 mb-2">No hay datos de distribución</p>
            <p className="text-gray-400 text-sm">
              Agrega inversiones para ver la distribución de activos
            </p>
          </div>
        )}
      </div>

      {/* Lista de Activos - Vista Previa/Completa */}
      <div className="bg-white rounded-2xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">Tus Activos</h2>
          <span className="text-sm text-gray-500">
            {investments.length} activo{investments.length !== 1 ? 's' : ''} en total
          </span>
        </div>

        {investments.length > 0 ? (
          <>
            {/* Lista de inversiones */}
            <div className="space-y-3">
              {displayedInvestments.map((investment) => {
                const currentValue = investment.current_value || 0;
                const gain = investment.gain || 0;
                const roi = investment.roi || 0;

                return (
                  <div
                    key={investment.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                  >
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
                        <h3 className="font-semibold text-gray-900">
                          {investment.asset_name || investment.symbol}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {investment.symbol} • {formatAssetTypeName(investment.asset_type || 'otros')}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="font-bold text-gray-900">
                        {formatMoney(currentValue)}
                      </p>
                      <p className={`text-sm ${roi >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Botón para mostrar más/menos */}
            {shouldShowToggle && (
              <div className="mt-6 text-center">
                <button
                  onClick={() => setShowAllInvestments(!showAllInvestments)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#B59F50] text-white rounded-lg hover:bg-[#A68F45] transition-colors font-medium"
                >
                  {showAllInvestments ? (
                    <>
                      <FaChevronUp size={14} />
                      Mostrar menos
                    </>
                  ) : (
                    <>
                      <FaChevronDown size={14} />
                      Ver {investments.length - previewCount} activos más
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-gray-400 text-2xl">💼</span>
            </div>
            <p className="text-gray-500 mb-2">No hay inversiones registradas</p>
            <p className="text-gray-400 text-sm">
              Comienza agregando tu primera inversión
            </p>
          </div>
        )}
      </div>
    </section>
  );
}