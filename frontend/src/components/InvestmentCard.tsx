import React from "react";

export default function InvestmentCard({ item, onEdit, onDelete }: any) {
  const price = Number(item.current_price ?? 0);
  const currentValue = Number(item.current_value ?? item.quantity * price);
  const invested = Number(item.total_invested ?? item.buy_price * item.quantity);

  const gain = currentValue - invested;
  const roi = invested > 0 ? (gain / invested) * 100 : 0;

  const gainColor =
    gain > 0 ? "text-green-400" : gain < 0 ? "text-red-400" : "text-slate-300";

  return (
    <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl mb-4 flex justify-between items-center shadow-md">
      {/* Left Section */}
      <div>
        <div className="text-xs opacity-60 uppercase tracking-wider">
          {item.asset_type} • {item.asset_name ?? ""}
        </div>

        <div className="text-xl font-bold">{item.symbol}</div>

        <div className="text-sm opacity-70">
          Cantidad: <span className="font-semibold">{item.quantity}</span>
        </div>

        {/* Live price */}
        <div className="text-sm mt-1">
          Precio actual:{" "}
          <span className="font-semibold">${price.toLocaleString()}</span>
        </div>

        {/* Current value */}
        <div className="text-sm opacity-80">
          Valor actual:{" "}
          <span className="font-semibold">
            ${currentValue.toLocaleString()}
          </span>
        </div>

        {/* Gain / Loss */}
        <div className={`mt-1 text-sm font-semibold ${gainColor}`}>
          {gain >= 0 ? "+" : ""}
          {gain.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}{" "}
          USD{" "}
          <span className="opacity-70">
            ({roi.toFixed(2)}
            %)
          </span>
        </div>
      </div>

      {/* Right actions */}
      <div className="flex flex-col items-end gap-2">
        <button
          onClick={() => onEdit?.(item)}
          className="px-4 py-1 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm transition"
        >
          Editar
        </button>
        <button
          onClick={() => onDelete?.(item)}
          className="px-4 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-sm transition"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
