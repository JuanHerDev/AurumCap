"use client";

import React from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";

export default function Navbar() {
    const { user, logout } = useAuth();

    // 🚨 Si NO hay usuario, no mostrar la navbar
    if (!user) return null;

    return (
        <nav className="flex items-center justify-between p-4 bg-[#CCB661] text-white shadow-md">
            {/* Logo / Nombre */}
            <div className="font-bold text-3xl text-[#FFFFFF] drop-shadow-md border border-black px-3 py-1 rounded-md">
                AurumCap
            </div>

            {/* Opciones */}
            <div className="flex items-center gap-4">
                <div>{user.full_name || user.email}</div>

                <button
                    onClick={() => logout()}
                    className="bg-red-500 px-3 py-1 rounded-md hover:bg-red-600 transition"
                >
                    Cerrar sesión
                </button>
            </div>
        </nav>
    );
}

