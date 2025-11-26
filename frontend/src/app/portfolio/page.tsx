// app/portfolio/page.tsx
"use client";

import { useState, useMemo } from "react";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useLivePrices } from "@/hooks/useLivePrices";
import InvestmentModal from "@/components/portfolio/InvestmentModal";
import AssetDistribution from "@/components/portfolio/AssetDistribution";
import InvestmentList from "@/components/portfolio/InvestmentList";
import PortfolioHeader from "@/components/portfolio/PortfolioHeader";
import { 
  FaPlus, 
  FaSyncAlt, 
  FaChartPie, 
  FaList,
  FaHome,
  FaUser,
  FaBriefcase
} from "react-icons/fa";
import { useRouter } from "next/navigation";

export default function PortfolioPage() {
  const {
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
    loading: priceLoading,
    portfolioMetrics,
  } = useLivePrices(investments, 15000);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingInvestment, setEditingInvestment] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"distribution" | "list">("distribution");
  const router = useRouter();

  // Función para formatear dinero
  const formatMoney = (n: number) => {
    return n?.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    });
  };

  // Manejar creación/edición de inversiones
  const handleCreate = async (payload: any) => {
    try {
      await create(payload);
      setModalOpen(false);
    } catch (error) {
      console.error("Error creating investment:", error);
    }
  };

  const handleEdit = async (payload: any) => {
    if (!editingInvestment) return;
    try {
      await update(editingInvestment.id, payload);
      setModalOpen(false);
      setEditingInvestment(null);
    } catch (error) {
      console.error("Error updating investment:", error);
    }
  };

  const handleDelete = async (investment: any) => {
    if (!confirm(`¿Eliminar ${investment.symbol}?`)) return;
    try {
      await remove(investment.id);
    } catch (error) {
      console.error("Error deleting investment:", error);
    }
  };

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
          <p className="text-red-500 mb-4">Error cargando datos: {String(error)}</p>
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

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Header */}
      <PortfolioHeader 
        portfolioMetrics={portfolioMetrics}
        onRefresh={refresh}
        loading={loading || priceLoading}
        formatMoney={formatMoney}
      />

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Tabs de Navegación */}
        <div className="bg-white rounded-2xl p-1 shadow-sm mb-6">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab("distribution")}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-colors ${
                activeTab === "distribution"
                  ? "bg-[#B59F50] text-white"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <FaChartPie size={16} />
                <span>Distribución</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab("list")}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-colors ${
                activeTab === "list"
                  ? "bg-[#B59F50] text-white"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <FaList size={16} />
                <span>Lista</span>
              </div>
            </button>
          </div>
        </div>

        {/* Contenido de Tabs */}
        {activeTab === "distribution" ? (
          <AssetDistribution 
            investments={pricedInvestments}
            formatMoney={formatMoney}
          />
        ) : (
          <InvestmentList 
            investments={pricedInvestments}
            onEdit={(investment) => {
              setEditingInvestment(investment);
              setModalOpen(true);
            }}
            onDelete={handleDelete}
            formatMoney={formatMoney}
          />
        )}
      </div>

      {/* Floating Action Button */}
      <button
        onClick={() => {
          setEditingInvestment(null);
          setModalOpen(true);
        }}
        className="fixed bottom-20 right-6 w-14 h-14 bg-[#B59F50] text-white rounded-full shadow-lg hover:bg-[#A68F45] transition-all duration-300 hover:scale-110 flex items-center justify-center"
        disabled={loading}
      >
        <FaPlus size={20} />
      </button>

      {/* Modal de Inversión */}
      <InvestmentModal
        open={modalOpen}
        investment={editingInvestment}
        onClose={() => {
          setModalOpen(false);
          setEditingInvestment(null);
        }}
        onSubmit={editingInvestment ? handleEdit : handleCreate}
      />
    </div>
  );
}