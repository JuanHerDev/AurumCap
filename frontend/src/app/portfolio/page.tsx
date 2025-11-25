// src/app/portfolio/page.tsx
"use client";

import React, { useState, useMemo } from "react";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useLivePrices } from "@/hooks/useLivePrices";
import InvestmentForm from "@/components/InvestmentForm";
import { GroupedInvestmentsModal } from "@/components/GroupedInvestmentsModal";
import {
  FaPlus,
  FaSyncAlt,
  FaChartPie,
  FaBriefcase,
  FaHome,
  FaUser,
  FaFilter,
} from "react-icons/fa";
import { useRouter } from "next/navigation";

function formatMoney(n: number) {
  return n?.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
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

// Componente para el gráfico de torta
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
            {formatMoney(totalValue)}
          </div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
      </div>
    </div>
  );
};

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

export default function PortfolioPage() {
  const {
    summary,
    investments,
    loading,
    error,
    refresh,
    create,
    update,
    remove,
  } = usePortfolio();

  const {
    investments: pricedInvestments,
    prices,
    loading: priceLoading,
    portfolioMetrics,
  } = useLivePrices(investments, 15000);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"grouped" | "list">("list");
  const [assetFilter, setAssetFilter] = useState<string>("all");
  const router = useRouter();

  // Calcular distribución REAL de activos basada en tus inversiones
  const realAssetDistribution = useMemo(() => {
    if (!pricedInvestments?.length) return [];

    // Agrupar por tipo de activo y calcular totales
    const assetMap = new Map();

    pricedInvestments.forEach((investment) => {
      const type = investment.asset_type || "otros";
      // USAR EL VALOR ACTUAL CALCULADO POR EL BACKEND
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
  }, [pricedInvestments]);

  // Filtrar inversiones por tipo de activo
  const filteredInvestments = useMemo(() => {
    if (!pricedInvestments?.length) return [];

    if (assetFilter === "all") {
      return pricedInvestments;
    }

    return pricedInvestments.filter(
      (investment) => investment.asset_type === assetFilter
    );
  }, [pricedInvestments, assetFilter]);

  // Obtener tipos de activos únicos de las inversiones
  const availableAssetTypes = useMemo(() => {
    if (!pricedInvestments?.length) return [];

    const types = new Set(
      pricedInvestments.map((inv) => inv.asset_type || "otros")
    );
    return Array.from(types);
  }, [pricedInvestments]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 text-sm">Cargando portafolio…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">
            Error cargando datos: {String(error.message)}
          </p>
          <button
            onClick={() => refresh?.()}
            className="px-4 py-2 bg-[#B59F50] text-black rounded-lg hover:bg-[#A68F45] transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  async function handleCreate(payload: any) {
    console.log(
      "📤 Creando inversión con payload:",
      JSON.stringify(payload, null, 2)
    );

    try {
      const result = await create(payload);
      console.log("✅ Inversión creada exitosamente:", result);
      setFormError(null);
      return result;
    } catch (err: any) {
      console.error("❌ Error completo al crear inversión:", err);

      let backendError = "Error del servidor";

      if (err.message) {
        backendError = err.message;
      } else if (err.responseData) {
        if (Array.isArray(err.responseData.detail)) {
          backendError = err.responseData.detail
            .map((error: any) => {
              const field = error.loc?.join(".") || "campo";
              return `${field}: ${error.msg}`;
            })
            .join(", ");
        } else if (err.responseData.detail) {
          backendError =
            typeof err.responseData.detail === "string"
              ? err.responseData.detail
              : JSON.stringify(err.responseData.detail);
        } else if (Array.isArray(err.responseData)) {
          backendError = err.responseData
            .map((error: any) => `${error.loc?.join(".")}: ${error.msg}`)
            .join(", ");
        } else {
          backendError = JSON.stringify(err.responseData);
        }
      }

      setFormError(backendError);
      throw err;
    }
  }

  async function handleEditSubmit(payload: any) {
    if (!editing) return;

    console.log(
      "📤 Editando inversión:",
      editing.id,
      JSON.stringify(payload, null, 2)
    );

    try {
      const result = await update(editing.id, payload);
      console.log("✅ Inversión actualizada exitosamente:", result);
      setFormError(null);
      return result;
    } catch (err: any) {
      console.error("❌ Error al actualizar inversión:", err);

      let backendError = "Error del servidor";

      if (err.responseData) {
        if (Array.isArray(err.responseData.detail)) {
          backendError = err.responseData.detail
            .map((error: any) => {
              const field = error.loc?.join(".") || "campo";
              return `${field}: ${error.msg}`;
            })
            .join(", ");
        } else if (err.responseData.detail) {
          backendError =
            typeof err.responseData.detail === "string"
              ? err.responseData.detail
              : JSON.stringify(err.responseData.detail);
        } else {
          backendError = JSON.stringify(err.responseData);
        }
      } else {
        backendError = err.message || "Error del servidor";
      }

      setFormError(backendError);
      throw err;
    }
  }

  async function onEdit(item: any) {
    setEditing(item);
    setModalOpen(true);
    setFormError(null);
  }

  async function onDelete(item: any) {
    if (!confirm(`¿Eliminar ${item.symbol}? Esta acción no se puede deshacer.`))
      return;
    try {
      await remove(item.id);
      setFormError(null);
    } catch (err: any) {
      console.error("❌ Error eliminando inversión:", err);
      setFormError(err.message || "Error al eliminar la inversión");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Header */}
      <header className="bg-white px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <FaBriefcase className="text-[#B59F50]" size={24} />
            <h1 className="text-2xl font-bold text-gray-900">Portafolio</h1>
          </div>
          <button
            onClick={() => refresh?.()}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={loading}
          >
            <FaSyncAlt size={16} className={loading ? "animate-spin" : ""} />
            <span className="text-sm font-medium">
              {loading ? "Actualizando..." : "Actualizar"}
            </span>
          </button>
        </div>
      </header>

      {/* Error Global */}
      {formError && (
        <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{formError}</p>
        </div>
      )}

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Asset Distribution - CON GRÁFICO DE TORTA */}
        <section className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-1">
                Distribución de Activos
              </h2>
              <p className="text-gray-500 text-sm">Resumen General</p>
            </div>
            {portfolioMetrics?.totalCurrentValue && (
              <div className="text-right">
                <p className="text-sm text-gray-500">Valor Total</p>
                <p className="text-xl font-bold text-[#B59F50]">
                  {formatMoney(portfolioMetrics.totalCurrentValue)}
                </p>
              </div>
            )}
          </div>

          {/* Gráfico de torta y leyenda */}
          {realAssetDistribution.length > 0 ? (
            <div className="flex flex-col lg:flex-row items-center lg:items-start gap-8">
              {/* Gráfico de torta */}
              <div className="shrink-0">
                <PieChart data={realAssetDistribution} />
              </div>

              {/* Leyenda de activos */}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                {realAssetDistribution.map((asset) => (
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
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
                <FaChartPie className="text-gray-400" size={24} />
              </div>
              <p className="text-gray-500">No hay datos de distribución</p>
              <p className="text-gray-400 text-sm mt-1">
                Agrega inversiones para ver la distribución
              </p>
            </div>
          )}
        </section>

        {/* Investment List */}
        <section className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              Tus Inversiones
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                {filteredInvestments?.length || 0} activos
                {assetFilter !== "all" &&
                  ` de ${formatAssetTypeName(assetFilter)}`}
              </span>
              {portfolioMetrics?.totalInvested && (
                <div className="text-right">
                  <p className="text-sm text-gray-500">Total Invertido</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatMoney(portfolioMetrics.totalInvested)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Filtro de tipos de activos */}
          {pricedInvestments?.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <FaFilter className="text-gray-400" size={16} />
                <span className="text-sm font-medium text-gray-700">
                  Filtrar por tipo:
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {assetTypeFilters
                  .filter((filter) => {
                    // Siempre mostrar "Todos los activos"
                    if (filter.value === "all") return true;

                    // Para otros filtros, verificar si hay al menos una inversión de ese tipo
                    return pricedInvestments.some((investment) => {
                      const investmentType = investment.asset_type || "otros";
                      return investmentType === filter.value;
                    });
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
          )}

          {filteredInvestments?.length ? (
            <div className="space-y-4">
              {filteredInvestments.map((investment: any) => {
                // USAR LOS VALORES CALCULADOS POR EL BACKEND
                const currentValue = investment.current_value || 0;
                const investedAmount = investment.invested_amount || 0;
                const gain = investment.gain || 0;
                const roi = investment.roi || 0;

                return (
                  <div
                    key={investment.id}
                    className="bg-linear-to-r from-gray-50 to-white rounded-xl p-5 hover:shadow-md transition-all duration-300 border border-gray-200 hover:border-gray-300"
                  >
                    <div className="flex justify-between items-center">
                      {/* Lado izquierdo - Información principal */}
                      <div className="flex items-center gap-4 flex-1">
                        <div className="w-12 h-12 bg-linear-to-br from-[#B59F50] to-[#A68F45] rounded-full flex items-center justify-center shadow-md">
                          <span className="text-white font-bold text-sm">
                            {investment.symbol?.charAt(0) ||
                              investment.asset_name?.charAt(0) ||
                              "A"}
                          </span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="font-bold text-gray-900 text-lg">
                              {investment.asset_name || investment.symbol}
                            </h3>
                            <span className="text-gray-500 font-mono text-sm">
                              {investment.symbol}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            {investment.quantity && (
                              <span>
                                Cantidad: <strong>{investment.quantity}</strong>
                              </span>
                            )}
                            {investment.asset_type && (
                              <span className="capitalize">
                                • {formatAssetTypeName(investment.asset_type)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Lado derecho - Valores DEL BACKEND */}
                      <div className="text-right">
                        {/* Porcentaje de rendimiento */}
                        <div
                          className={`text-lg font-bold mb-1 ${
                            gain >= 0 ? "text-green-500" : "text-red-500"
                          }`}
                        >
                          {gain >= 0 ? "+" : ""}
                          {roi.toFixed(2)}% hoy
                        </div>

                        {/* VALOR ACTUAL DE LA INVERSIÓN - CALCULADO POR BACKEND */}
                        <div className="text-2xl font-bold text-gray-900 mb-1">
                          {formatMoney(currentValue)}
                        </div>

                        {/* PRECIO ACTUAL POR ACCIÓN */}
                        <div className="text-sm text-gray-500">
                          Precio:{" "}
                          {formatMoney(
                            investment.current_price ||
                              investment.purchase_price ||
                              0
                          )}
                        </div>

                        {/* Ganancia/Pérdida en valor absoluto */}
                        {gain !== 0 && (
                          <div
                            className={`text-xs mt-1 ${
                              gain >= 0 ? "text-green-500" : "text-red-500"
                            }`}
                          >
                            {gain >= 0 ? "▲" : "▼"}
                            {formatMoney(Math.abs(gain))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Barra de acciones - Solo mostrar para inversiones reales */}
                    {investment.id && (
                      <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200">
                        <button
                          onClick={() => onEdit(investment)}
                          disabled={loading}
                          className="flex-1 py-2 text-sm bg-[#B59F50] text-white rounded-lg hover:bg-[#A68F45] transition-colors disabled:opacity-50 font-medium"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => onDelete(investment)}
                          disabled={loading}
                          className="flex-1 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 font-medium"
                        >
                          Eliminar
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              {assetFilter === "all" ? (
                <>
                  <FaBriefcase
                    className="mx-auto text-gray-300 mb-4"
                    size={48}
                  />
                  <p className="text-gray-500 mb-2">
                    No hay inversiones registradas
                  </p>
                  <p className="text-gray-400 text-sm mb-6">
                    Comienza agregando tu primera inversión
                  </p>
                  <button
                    onClick={() => setModalOpen(true)}
                    className="px-6 py-3 bg-[#B59F50] text-black font-semibold rounded-lg hover:bg-[#A68F45] transition-colors"
                  >
                    Agregar Primera Inversión
                  </button>
                </>
              ) : (
                <>
                  <FaFilter className="mx-auto text-gray-300 mb-4" size={48} />
                  <p className="text-gray-500 mb-2">
                    No hay inversiones de {formatAssetTypeName(assetFilter)}
                  </p>
                  <p className="text-gray-400 text-sm mb-6">
                    {availableAssetTypes.length > 0
                      ? `Prueba con otro filtro o agrega una inversión de ${formatAssetTypeName(
                          assetFilter
                        )}`
                      : "Agrega inversiones para ver los filtros disponibles"}
                  </p>
                  <button
                    onClick={() => setAssetFilter("all")}
                    className="px-6 py-3 bg-[#B59F50] text-black font-semibold rounded-lg hover:bg-[#A68F45] transition-colors"
                  >
                    Ver todos los activos
                  </button>
                </>
              )}
            </div>
          )}
        </section>
      </div>

      {/* Floating Action Button */}
      {pricedInvestments?.length > 0 && (
        <button
          onClick={() => {
            setEditing(null);
            setModalOpen(true);
            setFormError(null);
          }}
          className="fixed bottom-20 right-6 w-14 h-14 bg-[#B59F50] text-white rounded-full shadow-lg hover:bg-[#A68F45] transition-all duration-300 hover:scale-110 flex items-center justify-center"
          disabled={loading}
        >
          <FaPlus size={20} />
        </button>
      )}

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-3 px-8">
        <div className="flex justify-between items-center">
          <button
            onClick={() => router.push("/dashboard")}
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FaHome size={20} />
            <span className="text-xs font-medium">Inicio</span>
          </button>
          <button className="flex flex-col items-center gap-1 text-[#B59F50] transition-colors">
            <FaBriefcase size={20} />
            <span className="text-xs font-medium">Portafolio</span>
          </button>
          <button
            onClick={() => router.push("/simulator")}
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FaChartPie size={20} />
            <span className="text-xs font-medium">Simulador</span>
          </button>
          <button
            onClick={() => router.push("/profile")}
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FaUser size={20} />
            <span className="text-xs font-medium">Perfil</span>
          </button>
        </div>
      </nav>

      {/* Modal de formulario */}
      <InvestmentForm
        open={modalOpen}
        initial={editing}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
          setFormError(null);
        }}
        onSubmit={async (payload: any) => {
          try {
            if (editing) {
              await handleEditSubmit(payload);
            } else {
              await handleCreate(payload);
            }
            setModalOpen(false);
            setEditing(null);
            setFormError(null);
          } catch (err: any) {
            console.error("Error en onSubmit del modal:", err);
          }
        }}
      />
    </div>
  );
}
