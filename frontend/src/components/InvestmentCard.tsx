import React from "react";

export default function InvestmentCard({ item, onEdit, onDelete }: any) {
  const price = Number(item.current_price ?? 0);
  const value = Number(item.current_value ?? (item.quantity * price));
  return (
    <div className="bg-slate-800 p-4 rounded-lg mb-3 flex items-center justify-between">
      <div>
        <div className="text-sm opacity-70">{item.asset_type?.toUpperCase()} • {item.asset_name ?? ""}</div>
        <div className="font-semibold text-lg">{item.symbol}</div>
        <div className="text-sm opacity-60">Cantidad: {item.quantity} • Valor actual: ${value.toLocaleString()}</div>
      </div>

      <div className="flex items-center gap-2">
        <button onClick={() => onEdit?.(item)} className="px-3 py-1 rounded bg-slate-700 text-sm">Editar</button>
        <button onClick={() => onDelete?.(item)} className="px-3 py-1 rounded bg-rose-600 text-sm">Eliminar</button>
      </div>
    </div>
  );
}
