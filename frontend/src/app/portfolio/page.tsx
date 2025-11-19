"use client";

import React from "react";
import { usePortfolio } from "@/hooks/usePortfolio";
import InvestmentCard from "@/components/InvestmentCard";
import type { PortfolioSummary } from "@/types/investment";

function formatMoney(n: number) {
  return n?.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2});
}

export default function PortfolioPage() {
  const { summary, loading, error, refresh } = usePortfolio(15000);

  if (loading) return <div style={{padding:20}}>Cargando portafolio…</div>;
  if (error) return <div style={{padding:20}}>Error cargando datos: {String(error.message)}</div>;

  const s = summary as PortfolioSummary | undefined;

  return (
    <div style={{padding:20, maxWidth:900, margin:"0 auto", background:"#071026", minHeight:"100vh", color:"#fff"}}>
      <header style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18}}>
        <h1 style={{margin:0}}>Portafolio</h1>
        <div>
          <button onClick={() => refresh?.()} style={{padding:"8px 12px", borderRadius:8}}>Actualizar</button>
        </div>
      </header>

      {/* Top KPIs card */}
      <section style={{display:"grid", gridTemplateColumns:"1fr 320px", gap:16, marginBottom:16}}>
        <div style={{background:"#0b1320", padding:16, borderRadius:12}}>
          <h3 style={{marginTop:0}}>Distribución de Activos</h3>
          {/* Placeholder donut - puedes integrar recharts o chart.js */}
          <div style={{height:200, display:"flex", alignItems:"center", justifyContent:"center"}}>
            <img src={"/mnt/data/e0773c5a-ad77-4bdb-aa10-e3c6bb6b84fd.png"} alt="mock" style={{maxHeight:160, opacity:0.15}}/>
            {/* recomiendo usar recharts PieChart para distribución real */}
          </div>
        </div>

        <div style={{background:"#0b1320", padding:16, borderRadius:12}}>
          <div style={{display:"flex", justifyContent:"space-between", alignItems:"baseline"}}>
            <div>
              <div style={{fontSize:12, opacity:.7}}>Valor Actual</div>
              <div style={{fontSize:22, fontWeight:700}}>{formatMoney(s?.current_value ?? 0)}</div>
            </div>
            <div style={{textAlign:"right"}}>
              <div style={{fontSize:12, opacity:.7}}>Invertido</div>
              <div style={{fontSize:18}}>{formatMoney(s?.total_invested ?? 0)}</div>
            </div>
          </div>

          <div style={{marginTop:12}}>
            <div style={{fontSize:12, opacity:.7}}>Ganancia / Pérdida</div>
            <div style={{fontWeight:700, fontSize:16, marginTop:6, color: (s && s.gain_loss >= 0) ? "#16a34a" : "#ef4444"}}>{formatMoney(s?.gain_loss ?? 0)} ({s?.roi?.toFixed(2)}%)</div>
          </div>
        </div>
      </section>

      {/* List of investments */}
      <section>
        {s?.items?.length ? s.items.map((it) => (
          <InvestmentCard key={it.symbol} item={it} />
        )) : <div style={{opacity:.7}}>No hay inversiones registradas.</div>}
      </section>

      {/* Floating add button */}
      <button style={{
        position:"fixed",
        right:20,
        bottom:20,
        width:56,
        height:56,
        borderRadius:28,
        background:"#f59e0b",
        border:"none",
        boxShadow:"0 6px 18px rgba(0,0,0,0.4)",
        fontSize:28,
        color:"#071026"
      }}>+</button>
    </div>
  );
}
