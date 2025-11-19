import React from "react";
import type { InvestmentItem } from "../types/investment";

function formatMoney(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });
}

export default function InvestmentCard({ item }: { item: InvestmentItem }) {
  const changePerc = item.current_value && item.quantity ? ((item.current_price * item.quantity - (item.current_value - 0)) / (item.current_value || 1)) : 0;
  // We will display minimal sparkline using inline SVG placeholder
  const up = Math.random() > 0.5; // placeholder for sparkline direction; you can replace with real small chart component

  return (
    <div className="inv-card" style={{
      background: "#0f1724",
      color: "#fff",
      borderRadius: 12,
      padding: 14,
      marginBottom: 12,
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center"
    }}>
      <div style={{flex:1}}>
        <div style={{fontWeight:700}}>{item.asset_name} <span style={{opacity:.7, fontWeight:500}}>({item.symbol})</span></div>
        <div style={{opacity:.8, marginTop:6}}>
          {formatMoney(item.current_value)} <span style={{marginLeft:8, color: up ? "#16a34a" : "#ef4444"}}>{up ? "+0.8% hoy" : "-1.2% hoy"}</span>
        </div>
      </div>
      <div style={{width:110, textAlign:"right"}}>
        <div style={{fontSize:12, opacity:.8}}>{formatMoney(item.current_price)}</div>
        <div style={{marginTop:8}}>
          {/* tiny sparkline SVG */}
          <svg width="90" height="30" viewBox="0 0 90 30" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points={up ? "5,20 25,14 45,12 65,8 85,6" : "5,8 25,12 45,14 65,18 85,22"} stroke={up ? "#fbbf24" : "#ef4444"} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  );
}
