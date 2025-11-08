"use client";

import React from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";

export default function Navbar() {
    const { user, logout } = useAuth();
    return (
        <nav className="flex items-center justify-between p-4 bg-gray-900 text-white">
            <div className="font-bold text-3xl text-yellow-400">AurumCap</div>
            <div className="flex items-center gap-4">
                {user ? (
                    <>
                        <div>{user.full_name || user.email}</div>
                        <button onClick={() => logout()} className="bg-red-500 px-3 py-1">Cerrar sesión</button>
                    </>
                ) : (
                    <a href="/login">Entrar</a>
                )}
            </div>
        </nav>
    );
}