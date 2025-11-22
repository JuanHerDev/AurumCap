"use client";

import React, { useState, useEffect } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<any>;
  initial?: any;
};

export default function InvestmentForm({ open, onClose, onSubmit, initial }: Props) {
  const [form, setForm] = useState<any>({
    symbol: "",
    asset_name: "",
    asset_type: "crypto",
    quantity: "",
    invested_amount: "",
    purchase_price: "",
    currency: "USD",
    platform_id: null,
    date_acquired: "",
    coingecko_id: "",
    twelvedata_id: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initial) {
      // map numbers to strings for controlled inputs
      setForm({
        ...form,
        ...initial,
        quantity: initial.quantity ?? "",
        invested_amount: initial.invested_amount ?? "",
        purchase_price: initial.purchase_price ?? "",
        platform_id: initial.platform_id ?? null,
        date_acquired: initial.date_acquired ? new Date(initial.date_acquired).toISOString().slice(0, 10) : "",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial]);

  function onChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setForm((s: any) => ({ ...s, [name]: value }));
  }

  async function submit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      // transform numeric fields
      const payload: any = {
        ...form,
        quantity: form.quantity === "" ? null : Number(form.quantity),
        invested_amount: form.invested_amount === "" ? null : Number(form.invested_amount),
        purchase_price: form.purchase_price === "" ? null : Number(form.purchase_price),
        platform_id: form.platform_id === "" ? null : form.platform_id,
        date_acquired: form.date_acquired ? new Date(form.date_acquired).toISOString() : undefined,
      };
      const res = await onSubmit(payload);
      onClose();
      return res;
    } catch (err: any) {
      setError(err.message || "Error");
      throw err;
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={() => onClose()} />
      <form
        onSubmit={submit}
        className="relative z-10 w-full max-w-2xl bg-slate-900 text-white rounded-2xl p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{initial ? "Editar inversión" : "Nueva inversión"}</h3>
          <button type="button" className="text-sm opacity-70" onClick={() => onClose()}>Cerrar</button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm opacity-80">Símbolo</label>
            <input name="symbol" value={form.symbol} onChange={onChange} required className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div>
            <label className="block text-sm opacity-80">Nombre del activo</label>
            <input name="asset_name" value={form.asset_name} onChange={onChange} className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div>
            <label className="block text-sm opacity-80">Tipo</label>
            <select name="asset_type" value={form.asset_type} onChange={onChange} className="mt-1 w-full p-2 rounded bg-slate-800">
              <option value="crypto">Crypto</option>
              <option value="stock">Stock</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm opacity-80">Moneda</label>
            <input name="currency" value={form.currency} onChange={onChange} className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div>
            <label className="block text-sm opacity-80">Cantidad</label>
            <input name="quantity" value={form.quantity} onChange={onChange} type="number" step="any" className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div>
            <label className="block text-sm opacity-80">Invertido (total)</label>
            <input name="invested_amount" value={form.invested_amount} onChange={onChange} type="number" step="any" className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div>
            <label className="block text-sm opacity-80">Precio compra (opcional)</label>
            <input name="purchase_price" value={form.purchase_price} onChange={onChange} type="number" step="any" className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div>
            <label className="block text-sm opacity-80">Fecha adquirida</label>
            <input name="date_acquired" value={form.date_acquired} onChange={onChange} type="date" className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>

          <div className="col-span-2">
            <label className="block text-sm opacity-80">Coingecko id (opcional)</label>
            <input name="coingecko_id" value={form.coingecko_id} onChange={onChange} className="mt-1 w-full p-2 rounded bg-slate-800" />
          </div>
        </div>

        {error && <div className="mt-3 text-sm text-rose-400">{error}</div>}

        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={() => onClose()} className="px-4 py-2 rounded bg-slate-700">Cancelar</button>
          <button type="submit" disabled={submitting} className="px-4 py-2 rounded bg-amber-500 text-slate-900 font-semibold">
            {submitting ? "Guardando..." : (initial ? "Guardar cambios" : "Crear inversión")}
          </button>
        </div>
      </form>
    </div>
  );
}
