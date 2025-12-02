"use client";

import { useState } from "react";
import { usePortfolio } from "@/hooks/usePortfolio";
import InvestmentModal from "@/components/portfolio/InvestmentModal";
import AssetDistribution from "@/components/portfolio/AssetDistribution";
import InvestmentList from "@/components/portfolio/InvestmentList";
import PortfolioHeader from "@/components/portfolio/PortfolioHeader";
import { FaPlus } from "react-icons/fa";

export default function PortfolioPage() {
  const {
    investments,
    summary,
    allocations,
    loading,
    error,
    refresh,
    createInvestment,
    updateInvestment,
    deleteInvestment,
    portfolioMetrics,
  } = usePortfolio();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingInvestment, setEditingInvestment] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"distribution" | "list">("distribution");

  // Format money function
  const formatMoney = (n: number) => {
    return n?.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    });
  };

  // Handle create investment
  const handleCreate = async (payload: any) => {
    try {
      await createInvestment(payload);
      setModalOpen(false);
    } catch (error) {
      console.error("Error creating investment:", error);
    }
  };

  // Handle edit investment
  const handleEdit = async (payload: any) => {
    if (!editingInvestment) return;
    try {
      await updateInvestment(editingInvestment.id, payload);
      setModalOpen(false);
      setEditingInvestment(null);
    } catch (error) {
      console.error("Error updating investment:", error);
    }
  };

  // Handle delete investment
  const handleDelete = async (investment: any) => {
    if (!confirm(`Are you sure you want to delete ${investment.symbol}?`)) return;
    try {
      await deleteInvestment(investment.id);
    } catch (error) {
      console.error("Error deleting investment:", error);
    }
  };

  if (loading && !investments.length) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 text-sm">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (error && !investments.length) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">Error loading portfolio: {error.message}</p>
          <button
            onClick={refresh}
            className="px-4 py-2 bg-[#B59F50] text-white rounded-lg hover:bg-[#A68F45] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Header */}
      <PortfolioHeader 
        portfolioMetrics={portfolioMetrics || {
          totalInvested: summary?.total_invested || 0,
          totalCurrentValue: summary?.total_value || 0,
          totalGain: summary?.total_gain || 0,
          totalROI: summary?.total_roi || 0,
        }}
        onRefresh={refresh}
        loading={loading}
        formatMoney={formatMoney}
      />

      {/* Main Content */}
      <div className="p-4 max-w-6xl mx-auto">
        {/* Navigation Tabs */}
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
              Distribution
            </button>
            <button
              onClick={() => setActiveTab("list")}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-colors ${
                activeTab === "list"
                  ? "bg-[#B59F50] text-white"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              List
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "distribution" ? (
          <AssetDistribution 
            investments={investments}
            formatMoney={formatMoney}
          />
        ) : (
          <InvestmentList 
            investments={investments}
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

      {/* Investment Modal */}
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