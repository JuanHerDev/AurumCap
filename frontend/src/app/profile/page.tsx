import React from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";

export default function ProfilePage() {
    const { user, loading } = useAuth();
    if (loading) return <div>Cargando...</div>
    if (!user) return <div>No autenticado</div>;

    return (
        <main className="p-6">
            <h1 className="text-xl font-bold">Perfil</h1>
            <p>Email: {user.email}</p>
            <p>Nombre: {user.full_name || "-"}</p>
            <p>Rol: {user.role}</p>
        </main>
    );
}