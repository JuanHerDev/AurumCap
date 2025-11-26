// components/portfolio/InvestmentModal.tsx
import { useState, useEffect } from "react";
import { FaTimes, FaCalculator } from "react-icons/fa";

interface InvestmentModalProps {
  open: boolean;
  investment: any | null;
  onClose: () => void;
  onSubmit: (payload: any) => void;
}

// Plataformas de inversión comunes
const INVESTMENT_PLATFORMS = [
  { value: "binance", label: "Binance", category: "crypto" },
  { value: "hapi", label: "Hapi", category: "crypto" },
  { value: "etoro", label: "eToro", category: "multi" },
  { value: "interactive_brokers", label: "Interactive Brokers", category: "stocks" },
  { value: "td_ameritrade", label: "TD Ameritrade", category: "stocks" },
  { value: "coinbase", label: "Coinbase", category: "crypto" },
  { value: "kraken", label: "Kraken", category: "crypto" },
  { value: "fidelity", label: "Fidelity", category: "stocks" },
  { value: "vanguard", label: "Vanguard", category: "stocks" },
  { value: "metatrader", label: "MetaTrader", category: "forex" },
  { value: "other", label: "Otra Plataforma", category: "other" },
];

// Estrategias de inversión
const INVESTMENT_STRATEGIES = [
  { value: "dca", label: "DCA (Promedio de Costo en Dólares)" },
  { value: "lump_sum", label: "Inversión Única" },
  { value: "swing_trading", label: "Swing Trading" },
  { value: "day_trading", label: "Day Trading" },
  { value: "long_term", label: "Inversión a Largo Plazo" },
  { value: "arbitrage", label: "Arbitraje" },
  { value: "other", label: "Otra Estrategia" },
];

export default function InvestmentModal({
  open,
  investment,
  onClose,
  onSubmit,
}: InvestmentModalProps) {
  const [formData, setFormData] = useState({
    symbol: "",
    asset_name: "",
    asset_type: "stock",
    quantity: "",
    purchase_price: "",
    invested_amount: "", // NUEVO: Cantidad total invertida en USD
    currency: "USD",
    platform: "", // NUEVO: Plataforma de inversión
    strategy: "", // NUEVO: Estrategia de inversión
    transaction_date: new Date().toISOString().split('T')[0], // NUEVO: Fecha de transacción
    notes: "",
  });

  const [loading, setLoading] = useState(false);
  const [calculatedTotal, setCalculatedTotal] = useState(0);

  // Calcular total automáticamente cuando cambian cantidad o precio
  useEffect(() => {
    const quantity = parseFloat(formData.quantity) || 0;
    const price = parseFloat(formData.purchase_price) || 0;
    const total = quantity * price;
    setCalculatedTotal(total);
    
    // Auto-completar invested_amount si está vacío o coincide con el cálculo anterior
    if (!formData.invested_amount || parseFloat(formData.invested_amount) === calculatedTotal) {
      setFormData(prev => ({
        ...prev,
        invested_amount: total > 0 ? total.toString() : ""
      }));
    }
  }, [formData.quantity, formData.purchase_price, calculatedTotal]);

  // Reset form when modal opens/closes or investment changes
  useEffect(() => {
    if (open) {
      if (investment) {
        // Editing existing investment
        setFormData({
          symbol: investment.symbol || "",
          asset_name: investment.asset_name || "",
          asset_type: investment.asset_type || "stock",
          quantity: investment.quantity?.toString() || "",
          purchase_price: investment.purchase_price?.toString() || "",
          invested_amount: investment.invested_amount?.toString() || "",
          currency: investment.currency || "USD",
          platform: investment.platform || "",
          strategy: investment.strategy || "",
          transaction_date: investment.transaction_date || new Date().toISOString().split('T')[0],
          notes: investment.notes || "",
        });
      } else {
        // Creating new investment
        setFormData({
          symbol: "",
          asset_name: "",
          asset_type: "stock",
          quantity: "",
          purchase_price: "",
          invested_amount: "",
          currency: "USD",
          platform: "",
          strategy: "",
          transaction_date: new Date().toISOString().split('T')[0],
          notes: "",
        });
      }
      setCalculatedTotal(0);
    }
  }, [open, investment]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        quantity: parseFloat(formData.quantity) || 0,
        purchase_price: parseFloat(formData.purchase_price) || 0,
        // Si no se especifica invested_amount, calcularlo automáticamente
        invested_amount: parseFloat(formData.invested_amount) || calculatedTotal,
      };

      await onSubmit(payload);
      onClose();
    } catch (error) {
      console.error("Error submitting form:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  // Filtrar plataformas por tipo de activo
  const filteredPlatforms = INVESTMENT_PLATFORMS.filter(platform => {
    if (formData.asset_type === 'crypto') {
      return platform.category === 'crypto' || platform.category === 'multi';
    } else if (formData.asset_type === 'stock') {
      return platform.category === 'stocks' || platform.category === 'multi';
    }
    return true; // Para otros tipos, mostrar todas las plataformas
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            {investment ? "Editar Inversión" : "Agregar Inversión"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <FaTimes size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Símbolo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Símbolo *
            </label>
            <input
              type="text"
              name="symbol"
              value={formData.symbol}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              placeholder="Ej: AAPL, BTC, TSLA"
            />
          </div>

          {/* Nombre del Activo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nombre del Activo
            </label>
            <input
              type="text"
              name="asset_name"
              value={formData.asset_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              placeholder="Ej: Apple Inc., Bitcoin, Tesla Inc."
            />
          </div>

          {/* Tipo de Activo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de Activo *
            </label>
            <select
              name="asset_type"
              value={formData.asset_type}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
            >
              <option value="stock">Acciones</option>
              <option value="crypto">Criptomonedas</option>
              <option value="bond">Renta Fija</option>
              <option value="real_estate">Inmuebles</option>
              <option value="commodity">Commodities</option>
              <option value="cash">Efectivo</option>
              <option value="otros">Otros</option>
            </select>
          </div>

          {/* Cantidad y Precio */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cantidad *
              </label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                required
                step="any"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Precio Unitario *
              </label>
              <input
                type="number"
                name="purchase_price"
                value={formData.purchase_price}
                onChange={handleChange}
                required
                step="any"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                placeholder="0.00"
              />
            </div>
          </div>

          {/* Cantidad Invertida (USD) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <div className="flex items-center gap-2">
                <FaCalculator size={14} />
                <span>Cantidad Invertida (USD) *</span>
              </div>
            </label>
            <input
              type="number"
              name="invested_amount"
              value={formData.invested_amount}
              onChange={handleChange}
              required
              step="any"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              placeholder="0.00"
            />
            {calculatedTotal > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Calculado: {calculatedTotal.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} 
                {Math.abs(calculatedTotal - parseFloat(formData.invested_amount || '0')) > 0.01 && (
                  <span className="text-orange-500 ml-2">
                    (diferencia con cálculo automático)
                  </span>
                )}
              </p>
            )}
          </div>

          {/* Plataforma de Inversión */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Plataforma de Inversión *
            </label>
            <select
              name="platform"
              value={formData.platform}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
            >
              <option value="">Selecciona una plataforma</option>
              {filteredPlatforms.map(platform => (
                <option key={platform.value} value={platform.value}>
                  {platform.label}
                </option>
              ))}
            </select>
          </div>

          {/* Estrategia de Inversión */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Estrategia de Inversión
            </label>
            <select
              name="strategy"
              value={formData.strategy}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
            >
              <option value="">Selecciona una estrategia</option>
              {INVESTMENT_STRATEGIES.map(strategy => (
                <option key={strategy.value} value={strategy.value}>
                  {strategy.label}
                </option>
              ))}
            </select>
          </div>

          {/* Fecha de Transacción */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fecha de Transacción
            </label>
            <input
              type="date"
              name="transaction_date"
              value={formData.transaction_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
            />
          </div>

          {/* Moneda */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Moneda de la Transacción *
            </label>
            <select
              name="currency"
              value={formData.currency}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
            >
              <option value="USD">USD - Dólar Americano</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - Libra Esterlina</option>
              <option value="MXN">MXN - Peso Mexicano</option>
              <option value="BTC">BTC - Bitcoin</option>
              <option value="ETH">ETH - Ethereum</option>
            </select>
          </div>

          {/* Notas */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notas
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
              placeholder="Notas adicionales sobre esta inversión, como propósito, condiciones, etc."
            />
          </div>

          {/* Botones de Acción */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 py-3 px-4 bg-[#B59F50] text-white rounded-lg hover:bg-[#A68F45] transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? "Guardando..." : investment ? "Actualizar" : "Agregar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}