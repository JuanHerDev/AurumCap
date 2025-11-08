"use client";

import React, { useState } from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";

export default function RegisterForm() {

    const { register } = useAuth();
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [err, setErr] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (password !== confirm) {
        setErr("Las contraseñas no coinciden");
        return;
    }
    setLoading(true);
    try {
        await register(email, password, name);
    } catch (error: any) {
        setErr(error?.response?.data?.detail || "Registro fallido");
    } finally {
        setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <input aria-label="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nombre (opcional)" />
      <input aria-label="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Correo electrónico" />
      <input aria-label="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Contraseña" />
      <input aria-label="confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Confirmar contraseña" />
      {err && <div className="text-red-500">{err}</div>}
      <button disabled={loading}>{loading ? "Registrando..." : "Registrarme"}</button>
      <div className="mt-2">
        <button type="button" onClick={() => alert("Google OAuth placeholder")} className="w-full">Continuar con Google</button>
      </div>
    </form>
  );
}