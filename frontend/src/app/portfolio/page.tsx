"use client";

import React, { useState } from "react";

import { usePortfolio } from "@/hooks/usePortfolio";
import { useLivePrices } from "@/hooks/useLivePrices";

import InvestmentCard from "@/components/InvestmentCard";
import InvestmentForm from "@/components/InvestmentForm";
import type { PortfolioSummary } from "@/types/investment";

function formatMoney(n: number) {
  return n?.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
}

export default function PortfolioPage() {
  // Backend crud data
  const {
    summary,
    investments,
    loading,
    error,
    refresh,
    create,
    update,
    remove,
  } = usePortfolio(); // ⬅ SIN POLLING

  // Live prices hook
  const {
    investments: pricedInvestments,
    prices,
    loading: priceLoading,
  } = useLivePrices(investments, 15000); // prices polling / 15s

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);

  if (loading) return <div style={{ padding: 20 }}>Cargando portafolio…</div>;
  if (error)
    return (
      <div style={{ padding: 20 }}>
        Error cargando datos: {String(error.message)}
      </div>
    );

  const s = summary as PortfolioSummary | undefined;

  async function handleCreate(payload: any) {
    return create(payload); // backend
  }

  async function handleEditSubmit(payload: any) {
    if (!editing) return;
    return update(editing.id, payload); // backend
  }

  async function onEdit(item: any) {
    setEditing(item);
    setModalOpen(true);
  }

  async function onDelete(item: any) {
    if (!confirm(`Eliminar ${item.asset}? Esto no se puede deshacer.`)) return;
    try {
      await remove(item.id);
    } catch (err: any) {
      alert("Error eliminando: " + (err.message || String(err)));
    }
  }

  return (
    <div
      style={{
        padding: 20,
        maxWidth: 900,
        margin: "0 auto",
        background: "#071026",
        minHeight: "100vh",
        color: "#fff",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 18,
        }}
      >
        <h1 style={{ margin: 0 }}>Portafolio</h1>

        <div>
          <button
            onClick={() => refresh?.()}
            style={{ padding: "8px 12px", borderRadius: 8 }}
          >
            Actualizar
          </button>
        </div>
      </header>

      {/* Summary */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 320px",
          gap: 16,
          marginBottom: 16,
        }}
      >
        <div style={{ background: "#0b1320", padding: 16, borderRadius: 12 }}>
          <h3 style={{ marginTop: 0 }}>Distribución de Activos</h3>
          <div
            style={{
              height: 200,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <img
              src={"Logo.png"}
              alt="mock"
              style={{ maxHeight: 160, opacity: 0.15 }}
            />
          </div>
        </div>

        <div style={{ background: "#0b1320", padding: 16, borderRadius: 12 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
            }}
          >
            <div>
              <div style={{ fontSize: 12, opacity: 0.7 }}>Valor Actual</div>
              <div style={{ fontSize: 22, fontWeight: 700 }}>
                {formatMoney(s?.current_value ?? 0)}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 12, opacity: 0.7 }}>Invertido</div>
              <div style={{ fontSize: 18 }}>
                {formatMoney(s?.total_invested ?? 0)}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 12, opacity: 0.7 }}>Ganancia / Pérdida</div>
            <div
              style={{
                fontWeight: 700,
                fontSize: 16,
                marginTop: 6,
                color:
                  s && s.gain_loss >= 0 ? "#16a34a" : "#ef4444",
              }}
            >
              {formatMoney(s?.gain_loss ?? 0)} ({s?.roi?.toFixed(2)}%)
            </div>
          </div>
        </div>
      </section>

      {/* Investment list */}
      <section>
        {pricedInvestments?.length ? (
          pricedInvestments.map((it: any) => (
            <InvestmentCard
              key={it.id}
              item={it}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))
        ) : (
          <div style={{ opacity: 0.7 }}>No hay inversiones registradas.</div>
        )}
      </section>

      {/* Floating btn */}
      <button
        title="Agregar inversión"
        onClick={() => {
          setEditing(null);
          setModalOpen(true);
        }}
        style={{
          position: "fixed",
          right: 20,
          bottom: 20,
          width: 56,
          height: 56,
          borderRadius: 28,
          background: "#f59e0b",
          border: "none",
          boxShadow: "0 6px 18px rgba(0,0,0,0.4)",
          fontSize: 28,
          color: "#071026",
        }}
      >
        +
      </button>

      {/* Modal */}
      <InvestmentForm
        open={modalOpen}
        initial={editing}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSubmit={async (payload: any) => {
          try {
            if (editing) {
              await handleEditSubmit(payload);
            } else {
              await handleCreate(payload);
            }
          } catch (err: any) {
            throw err;
          }
        }}
      />
    </div>
  );
}
