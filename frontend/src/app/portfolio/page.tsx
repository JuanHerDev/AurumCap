// src/app/portfolio/page.tsx
"use client";

import React, { useState } from "react";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useLivePrices } from "@/hooks/useLivePrices";
import InvestmentForm from "@/components/InvestmentForm";
import { FaPlus, FaSyncAlt, FaChartPie, FaBriefcase, FaHome, FaUser } from "react-icons/fa";
import { useRouter } from "next/navigation";

function formatMoney(n: number) {
  return n?.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
}

// Mock data para distribución de activos (puedes reemplazar con datos reales)
const assetTypes = [
  { name: "Renta Fija", color: "bg-blue-500" },
  { name: "Acciones", color: "bg-green-500" },
  { name: "Oro", color: "bg-yellow-500" },
  { name: "Cripto", color: "bg-purple-500" },
  { name: "Inmuebles", color: "bg-red-500" },
];

// Mock data para stocks populares (puedes reemplazar con tus investments reales)
const popularStocks = [
  { symbol: "GOOGL", name: "Google", change: "+2.5%", price: 12345.67 },
  { symbol: "AAPL", name: "Apple", change: "-1.2%", price: 9876.54 },
  { symbol: "MSFT", name: "Microsoft", change: "+0.8%", price: 15000.00 },
  { symbol: "TSLA", name: "Tesla", change: "-3.1%", price: 8123.45 },
  { symbol: "AMZN", name: "Amazon", change: "+1.9%", price: 11500.00 },
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
  } = useLivePrices(investments, 15000);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const router = useRouter();

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
          <p className="text-red-500 mb-4">Error cargando datos: {String(error.message)}</p>
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

  const s = summary as any;

  async function handleCreate(payload: any) {
  console.log("📤 Creando inversión con payload:", JSON.stringify(payload, null, 2));
  
  try {
    const result = await create(payload);
    console.log("✅ Inversión creada exitosamente:", result);
    setFormError(null);
    return result;
  } catch (err: any) {
      console.error("❌ Error completo al crear inversión:", err);
      console.error("❌ Status del error:", err.status);
      console.error("❌ Datos de respuesta:", err.responseData);
    
      // Mostrar error específico del backend con más detalles
      let backendError = "Error del servidor";
    
      if (err.message) {
        backendError = err.message;
      } else if (err.responseData) {
        if (Array.isArray(err.responseData.detail)) {
          // Errores de validación de Pydantic
          backendError = err.responseData.detail.map((error: any) => {
            const field = error.loc?.join('.') || 'campo';
            return `${field}: ${error.msg}`;
          }).join(', ');
        } else if (err.responseData.detail) {
          backendError = typeof err.responseData.detail === 'string' 
            ? err.responseData.detail 
            : JSON.stringify(err.responseData.detail);
        } else if (Array.isArray(err.responseData)) {
          backendError = err.responseData.map((error: any) => 
            `${error.loc?.join('.')}: ${error.msg}`
          ).join(', ');
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
    
    console.log("📤 Editando inversión:", editing.id, JSON.stringify(payload, null, 2));
    
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
          backendError = err.responseData.detail.map((error: any) => {
            const field = error.loc?.join('.') || 'campo';
            return `${field}: ${error.msg}`;
          }).join(', ');
        } else if (err.responseData.detail) {
          backendError = typeof err.responseData.detail === 'string' 
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
    if (!confirm(`¿Eliminar ${item.symbol}? Esta acción no se puede deshacer.`)) return;
    try {
      await remove(item.id);
      setFormError(null);
    } catch (err: any) {
      console.error("❌ Error eliminando inversión:", err);
      setFormError(err.message || "Error al eliminar la inversión");
    }
  }

  // Combinar investments reales con mock data para el demo
  const displayInvestments = pricedInvestments?.length > 0 ? pricedInvestments : popularStocks.map((stock, index) => ({
    id: index,
    symbol: stock.symbol,
    asset_name: stock.name,
    current_price: stock.price,
    change: stock.change,
    quantity: 1,
    current_value: stock.price,
    type: "stock"
  }));

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
        {/* Asset Distribution */}
        <section className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-1">Distribución de Activos</h2>
              <p className="text-gray-500 text-sm">Resumen General</p>
            </div>
            {s?.total_value && (
              <div className="text-right">
                <p className="text-sm text-gray-500">Valor Total</p>
                <p className="text-xl font-bold text-[#B59F50]">
                  {formatMoney(s.total_value)}
                </p>
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {assetTypes.map((asset, index) => (
              <div key={asset.name} className="text-center">
                <div className={`w-16 h-16 ${asset.color} rounded-full mx-auto mb-3 flex items-center justify-center`}>
                  <span className="text-white font-bold text-sm">
                    {asset.name.charAt(0)}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-900">{asset.name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatMoney((s?.current_value ?? 100000) * (0.1 + index * 0.05))}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Investment List */}
        <section className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Tus Inversiones</h2>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                {displayInvestments?.length || 0} activos
              </span>
              {s?.total_invested && (
                <div className="text-right">
                  <p className="text-sm text-gray-500">Total Invertido</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatMoney(s.total_invested)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {displayInvestments?.length ? (
            <div className="space-y-4">
              {displayInvestments.map((investment: any) => (
                <div key={investment.id} className="bg-gray-50 rounded-xl p-4 hover:shadow-md transition-shadow border border-gray-200">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-[#B59F50] rounded-full flex items-center justify-center">
                          <span className="text-white font-bold text-sm">
                            {investment.symbol?.charAt(0) || investment.asset_name?.charAt(0) || 'A'}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {investment.asset_name || investment.symbol}
                          </h3>
                          <p className="text-gray-500 text-sm">{investment.symbol}</p>
                          {investment.asset_type && (
                            <span className="inline-block px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded-full mt-1">
                              {investment.asset_type}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Información adicional para inversiones reales */}
                      {investment.id && (
                        <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                          {investment.quantity && (
                            <div>
                              <span className="text-gray-500">Cantidad:</span>
                              <span className="ml-2 font-medium">{investment.quantity}</span>
                            </div>
                          )}
                          {investment.invested_amount && (
                            <div>
                              <span className="text-gray-500">Invertido:</span>
                              <span className="ml-2 font-medium">
                                {formatMoney(investment.invested_amount)}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <div className={`text-sm font-semibold ${
                        investment.change?.includes('+') ? 'text-green-500' : 
                        investment.change?.includes('-') ? 'text-red-500' : 'text-gray-500'
                      }`}>
                        {investment.change || '+0.0%'} hoy
                      </div>
                      <div className="text-lg font-bold text-gray-900">
                        {formatMoney(investment.current_price || investment.current_value || investment.price)}
                      </div>
                      {investment.current_value && investment.invested_amount && (
                        <div className={`text-xs mt-1 ${
                          investment.current_value >= investment.invested_amount ? 'text-green-500' : 'text-red-500'
                        }`}>
                          {investment.current_value >= investment.invested_amount ? '▲' : '▼'} 
                          {formatMoney(Math.abs(investment.current_value - investment.invested_amount))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions for real investments */}
                  {investment.id && (
                    <div className="flex gap-2 mt-3 pt-3 border-t border-gray-200">
                      <button
                        onClick={() => onEdit(investment)}
                        disabled={loading}
                        className="flex-1 py-2 text-sm bg-[#B59F50] text-white rounded-lg hover:bg-[#A68F45] transition-colors disabled:opacity-50"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => onDelete(investment)}
                        disabled={loading}
                        className="flex-1 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50"
                      >
                        Eliminar
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FaBriefcase className="mx-auto text-gray-300 mb-4" size={48} />
              <p className="text-gray-500 mb-2">No hay inversiones registradas</p>
              <p className="text-gray-400 text-sm mb-6">
                Comienza agregando tu primera inversión
              </p>
              <button
                onClick={() => setModalOpen(true)}
                className="px-6 py-3 bg-[#B59F50] text-black font-semibold rounded-lg hover:bg-[#A68F45] transition-colors"
              >
                Agregar Primera Inversión
              </button>
            </div>
          )}
        </section>
      </div>

      {/* Floating Action Button */}
      {displayInvestments?.length > 0 && (
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
            onClick={() => router.push('/dashboard')} 
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
            onClick={() => router.push('/simulator')} 
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FaChartPie size={20} />
            <span className="text-xs font-medium">Simulador</span>
          </button>
          <button 
            onClick={() => router.push('/profile')} 
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FaUser size={20} />
            <span className="text-xs font-medium">Perfil</span>
          </button>
        </div>
      </nav>

      {/* Modal */}
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
            // Cerrar modal solo si es exitoso
            setModalOpen(false);
            setEditing(null);
            setFormError(null);
          } catch (err: any) {
            // El error ya se maneja en las funciones individuales
            console.error("Error en onSubmit del modal:", err);
            // No cerramos el modal para que el usuario pueda corregir los errores
          }
        }}
      />
    </div>
  );
}