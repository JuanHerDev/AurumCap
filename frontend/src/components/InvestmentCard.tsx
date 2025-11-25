"use client";

import React from "react";
import { FaEdit, FaTrash } from "react-icons/fa";
import { FiTrendingUp, FiTrendingDown } from "react-icons/fi";

function formatMoney(n: number) {
  return n?.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
}

export default function InvestmentCard({ 
  item, 
  onEdit, 
  onDelete 
}: { 
  item: any; 
  onEdit: (item: any) => void;
  onDelete: (item: any) => void;
}) {
  const currentPrice = item.current_price || item.purchase_price || 0;
  const invested = item.invested_amount || 0;
  const currentValue = item.current_value || (item.quantity * currentPrice);
  const gain = currentValue - invested;
  const roi = invested > 0 ? (gain / invested) * 100 : 0;

  const gainColor = gain > 0 ? "text-green-500" : gain < 0 ? "text-red-500" : "text-gray-500";

  return (
    <div className="bg-gray-50 rounded-xl p-4 hover:shadow-md transition-shadow border border-gray-200">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 text-lg">{item.symbol}</h3>
          <p className="text-gray-500 text-sm capitalize">{item.asset_name}</p>
          <p className="text-gray-400 text-xs capitalize">{item.asset_type}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(item)}
            className="p-2 text-gray-400 hover:text-[#B59F50] transition-colors"
          >
            <FaEdit size={16} />
          </button>
          <button
            onClick={() => onDelete(item)}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
          >
            <FaTrash size={16} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Cantidad</p>
          <p className="font-medium">{item.quantity} {item.symbol}</p>
        </div>
        <div>
          <p className="text-gray-500">Invertido</p>
          <p className="font-medium">{formatMoney(invested)}</p>
        </div>
        <div>
          <p className="text-gray-500">Valor Actual</p>
          <p className="font-medium">{formatMoney(currentValue)}</p>
        </div>
        <div>
          <p className="text-gray-500">Ganancia/Pérdida</p>
            {gain >= 0 ? (
              <FiTrendingUp className="text-green-500" size={14} />
            ) : (
              <FiTrendingDown className="text-red-500" size={14} />
            )}
            <span className={`font-medium ${gainColor}`}>
              {formatMoney(gain)} ({roi.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>
  );
}