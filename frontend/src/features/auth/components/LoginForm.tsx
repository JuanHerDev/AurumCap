"use client";

import React, { useState } from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";

export default function LoginForm() {
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [err, setErr] = useState<String | null>(null);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setErr(null);
        setLoading(true);

        try {
            await login(email, password);
        } catch (error: any) {
            setErr(error?.response?.data?.detail || "Login failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input aria-label="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="AurumCap@ejemplo.com" />
            <input aria-label="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Contraseña" />
            { err && <div className="text-red-500">{err}</div>}
            <button disabled={loading}>{loading ? "Cargando..." : "Entrar"}</button>
            <div className="mt-2">
                <button type="button" onClick={() => alert("Google OAuth placeholder")} className="w-full">
                    Continuar con Google
                </button>
            </div>
        </form>
    );
}