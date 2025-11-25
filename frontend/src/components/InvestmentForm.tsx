// src/components/InvestmentForm.tsx
"use client";

import React, { useState, useEffect } from "react";
import { AuthService } from "@/services/auth.service";
import { ApiInterceptor } from "@/services/api.interceptor";

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<any>;
  initial?: any;
};

// Configuración de API desde variables de entorno
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Opciones predefinidas para asset_type
const ASSET_TYPES = [
  { value: "stock", label: "Acciones" },
  { value: "crypto", label: "Criptomoneda" },
  { value: "etf", label: "ETF" },
  { value: "bond", label: "Bono" },
  { value: "real_estate", label: "Bienes Raíces" },
  { value: "other", label: "Otro" },
];

// Monedas soportadas
const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "MXN"];

// Interface para plataformas
interface Platform {
  id: number;
  name: string;
  display_name: string;
  type: string;
  supported_asset_types: string[];
}

export default function InvestmentForm({ open, onClose, onSubmit, initial }: Props) {
  const [form, setForm] = useState<any>({
    asset_type: "stock",
    symbol: "",
    asset_name: "",
    invested_amount: "",
    quantity: "",
    purchase_price: "",
    currency: "USD",
    platform_id: "",
    platform_specific_id: "",
    coingecko_id: "",
    twelvedata_id: "",
    notes: "",
  });
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loadingPlatforms, setLoadingPlatforms] = useState(false);

  // Cargar plataformas cuando cambia el tipo de activo
  useEffect(() => {
    if (open && form.asset_type) {
      loadPlatformsByAssetType(form.asset_type);
    }
  }, [open, form.asset_type]);

  // Reset form cuando se abre/cierra o cambia initial
  useEffect(() => {
    if (open) {
      if (initial) {
        setForm({
          asset_type: initial.asset_type || "stock",
          symbol: initial.symbol || "",
          asset_name: initial.asset_name || "",
          invested_amount: initial.invested_amount?.toString() || "",
          quantity: initial.quantity?.toString() || "",
          purchase_price: initial.purchase_price?.toString() || "",
          currency: initial.currency || "USD",
          platform_id: initial.platform_id?.toString() || "",
          platform_specific_id: initial.platform_specific_id || "",
          coingecko_id: initial.coingecko_id || "",
          twelvedata_id: initial.twelvedata_id || "",
          notes: initial.notes || "",
        });

        if (initial.asset_type) {
          loadPlatformsByAssetType(initial.asset_type);
        }
      } else {
        setForm({
          asset_type: "stock",
          symbol: "",
          asset_name: "",
          invested_amount: "",
          quantity: "",
          purchase_price: "",
          currency: "USD",
          platform_id: "",
          platform_specific_id: "",
          coingecko_id: "",
          twelvedata_id: "",
          notes: "",
        });
      }
      setError(null);
      setPlatforms([]);
    }
  }, [open, initial]);

  // FUNCIÓN COMPLETAMENTE CORREGIDA: Usar ApiInterceptor
  async function loadPlatformsByAssetType(assetType: string) {
    if (!open) return;
    
    setLoadingPlatforms(true);
    setError(null);
    
    try {
      console.log(`🔄 Cargando plataformas para: ${assetType}`);
      
      // URL corregida
      const url = `${API_BASE_URL}/platforms/by-asset-type/${assetType}?active_only=true`;
      console.log(`🌐 URL: ${url}`);
      
      // Usar ApiInterceptor en lugar de fetch directo
      const response = await ApiInterceptor.fetchWithAuth(url, {
        method: 'GET',
      });
      
      console.log(`📊 Response status: ${response.status}`);
      
      if (response.ok) {
        const platformsData = await response.json();
        console.log(`✅ Plataformas cargadas:`, platformsData);
        setPlatforms(platformsData);
      } else {
        console.error(`❌ Error HTTP ${response.status}`);
        throw new Error(`Error al cargar plataformas: ${response.status}`);
      }
    } catch (error: any) {
      console.error("❌ Error loading platforms:", error);
      
      // El ApiInterceptor ya maneja la redirección para errores 401
      // Solo mostramos el error si no es de autenticación
      if (error.message !== 'Authentication failed' && 
          error.message !== 'Authentication required' &&
          !error.message.includes('Authentication')) {
        setError('Error al cargar las plataformas. Usando opciones por defecto.');
      }
      
      // Usar plataformas por defecto como fallback
      console.log(`🔄 Usando plataformas por defecto`);
      setPlatforms(getDefaultPlatforms(assetType));
    } finally {
      setLoadingPlatforms(false);
    }
  }

  // FUNCIÓN: Plataformas por defecto como fallback
  function getDefaultPlatforms(assetType: string): Platform[] {
    const defaultPlatforms: Platform[] = [
      {
        id: 1,
        name: "binance",
        display_name: "Binance",
        type: "exchange",
        supported_asset_types: ["crypto"]
      },
      {
        id: 2,
        name: "coinbase",
        display_name: "Coinbase",
        type: "exchange", 
        supported_asset_types: ["crypto"]
      },
      {
        id: 3,
        name: "interactive_brokers",
        display_name: "Interactive Brokers",
        type: "broker",
        supported_asset_types: ["stock", "etf", "bond"]
      },
      {
        id: 4,
        name: "etoro",
        display_name: "eToro",
        type: "broker",
        supported_asset_types: ["stock", "crypto", "etf"]
      },
      {
        id: 5,
        name: "metamask", 
        display_name: "Metamask",
        type: "wallet",
        supported_asset_types: ["crypto"]
      },
      {
        id: 6, 
        name: "ledger",
        display_name: "Ledger",
        type: "wallet",
        supported_asset_types: ["crypto"]
      },
      {
        id: 7,
        name: "other",
        display_name: "Other",
        type: "other", 
        supported_asset_types: ["stock", "crypto", "etf", "bond", "real_estate", "other"]
      }
    ];

    // Filtrar por tipo de activo
    if (assetType !== "other") {
      return defaultPlatforms.filter(platform => 
        platform.supported_asset_types.includes(assetType)
      );
    }

    return defaultPlatforms;
  }

  function onChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    
    if (name === "asset_type") {
      setForm((s: any) => ({ 
        ...s, 
        [name]: value,
        platform_id: "",
        platform_specific_id: "" 
      }));
    } else {
      setForm((s: any) => ({ ...s, [name]: value }));
    }
  }

  async function submit(e?: React.FormEvent) {
  if (e) e.preventDefault();
  setSubmitting(true);
  setError(null);
  
  try {
    // Validaciones básicas mejoradas
    if (!form.symbol.trim()) {
      throw new Error("El símbolo es requerido");
    }
    if (!form.asset_name.trim()) {
      throw new Error("El nombre del activo es requerido");
    }
    if (!form.invested_amount || Number(form.invested_amount) <= 0) {
      throw new Error("El monto invertido debe ser mayor a 0");
    }
    if (!form.quantity || Number(form.quantity) <= 0) {
      throw new Error("La cantidad debe ser mayor a 0");
    }

    // Validar formato del símbolo
    const symbol = form.symbol.trim().toUpperCase();
    if (!/^[A-Z0-9-]+$/.test(symbol)) {
      throw new Error("El símbolo solo puede contener letras, números y guiones");
    }

    // Preparar payload con conversión explícita de tipos
    const investedAmount = parseFloat(form.invested_amount);
    const quantity = parseFloat(form.quantity);
    
    const payload: any = {
      asset_type: form.asset_type,
      symbol: symbol,
      asset_name: form.asset_name.trim(),
      invested_amount: investedAmount,
      quantity: quantity,
      currency: form.currency,
    };

    // Campos opcionales - solo incluirlos si tienen valor
    if (form.platform_id && form.platform_id !== "") {
      payload.platform_id = parseInt(form.platform_id);
    }
    if (form.platform_specific_id?.trim()) {
      payload.platform_specific_id = form.platform_specific_id.trim();
    }
    if (form.coingecko_id?.trim()) {
      payload.coingecko_id = form.coingecko_id.trim().toLowerCase();
    }
    if (form.twelvedata_id?.trim()) {
      payload.twelvedata_id = form.twelvedata_id.trim();
    }
    if (form.notes?.trim()) {
      payload.notes = form.notes.trim();
    }

    // Manejar purchase_price - REDONDEAR A 6 DECIMALES
    if (form.purchase_price && form.purchase_price !== "") {
      payload.purchase_price = parseFloat(parseFloat(form.purchase_price).toFixed(6));
    } else {
      // Calcular automáticamente si no se proporciona y REDONDEAR
      const calculatedPrice = investedAmount / quantity;
      payload.purchase_price = parseFloat(calculatedPrice.toFixed(6));
    }

    console.log("📤 Payload final para enviar:", JSON.stringify(payload, null, 2));
    await onSubmit(payload);
    
    // Cerrar el modal si es exitoso
    onClose();
    
  } catch (err: any) {
    console.error("❌ Error en submit:", err);
    setError(err.message || "Error al procesar el formulario");
    throw err;
  } finally {
    setSubmitting(false);
  }
}

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div 
        className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <form onSubmit={submit} className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              {initial ? "Editar Inversión" : "Nueva Inversión"}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={submitting}
            >
              ✕
            </button>
          </div>

          {/* Form Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Tipo de Activo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Activo *
              </label>
              <select
                name="asset_type"
                value={form.asset_type}
                onChange={onChange}
                required
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              >
                {ASSET_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Símbolo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Símbolo *
              </label>
              <input
                name="symbol"
                value={form.symbol}
                onChange={onChange}
                placeholder="Ej: AAPL, BTC, TSLA"
                required
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent uppercase disabled:opacity-50"
              />
            </div>

            {/* Nombre del Activo */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre del Activo *
              </label>
              <input
                name="asset_name"
                value={form.asset_name}
                onChange={onChange}
                placeholder="Ej: Apple Inc., Bitcoin, Tesla Inc."
                required
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
            </div>

            {/* Cantidad */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cantidad *
              </label>
              <input
                name="quantity"
                type="number"
                step="any"
                value={form.quantity}
                onChange={onChange}
                placeholder="Ej: 10, 0.5, 100"
                required
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
            </div>

            {/* Monto Invertido */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Monto Invertido (USD) *
              </label>
              <input
                name="invested_amount"
                type="number"
                step="0.01"
                value={form.invested_amount}
                onChange={onChange}
                placeholder="Ej: 1000.00"
                required
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
            </div>

            {/* Precio de Compra */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Precio de Compra (por unidad)
              </label>
              <input
                name="purchase_price"
                type="number"
                step="0.01"
                value={form.purchase_price}
                onChange={onChange}
                placeholder="Se calcula automáticamente si se deja vacío"
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
            </div>

            {/* Moneda */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Moneda
              </label>
              <select
                name="currency"
                value={form.currency}
                onChange={onChange}
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              >
                {CURRENCIES.map((currency) => (
                  <option key={currency} value={currency}>
                    {currency}
                  </option>
                ))}
              </select>
            </div>

            {/* Plataforma */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Plataforma
              </label>
              <select
                name="platform_id"
                value={form.platform_id}
                onChange={onChange}
                disabled={loadingPlatforms || submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              >
                <option value="">Seleccionar Plataforma</option>
                {platforms.map((platform) => (
                  <option key={platform.id} value={platform.id}>
                    {platform.display_name}
                  </option>
                ))}
              </select>
              {loadingPlatforms && (
                <p className="text-xs text-gray-500 mt-1">Cargando plataformas...</p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                {platforms.length} plataformas disponibles
              </p>
            </div>

            {/* ID Específico de Plataforma */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ID Específico de Plataforma
              </label>
              <input
                name="platform_specific_id"
                value={form.platform_specific_id}
                onChange={onChange}
                placeholder="Ej: binance_btc_wallet_001"
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
              <p className="text-xs text-gray-500 mt-1">
                ID único del activo en la plataforma seleccionada
              </p>
            </div>

            {/* CoinGecko ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CoinGecko ID
              </label>
              <input
                name="coingecko_id"
                value={form.coingecko_id}
                onChange={onChange}
                placeholder="Ej: bitcoin, ethereum"
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
            </div>

            {/* TwelveData ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                TwelveData ID
              </label>
              <input
                name="twelvedata_id"
                value={form.twelvedata_id}
                onChange={onChange}
                placeholder="Opcional"
                disabled={submitting}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent disabled:opacity-50"
              />
            </div>
          </div>

          {/* Notas */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas
            </label>
            <textarea
              name="notes"
              value={form.notes}
              onChange={onChange}
              placeholder="Notas adicionales sobre esta inversión..."
              rows={3}
              disabled={submitting}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent resize-none disabled:opacity-50"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-6 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-[#B59F50] text-white font-semibold rounded-lg hover:bg-[#A68F45] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? "Guardando..." : (initial ? "Actualizar" : "Crear Inversión")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}