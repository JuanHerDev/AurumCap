"use client";

import { useAuth } from "@/features/auth/context/AuthProvider";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-2xl mx-auto py-12 text-center">
      <h1 className="text-3xl font-semibold mb-4">Bienvenido {user?.full_name}</h1>
      <p className="text-gray-600 mb-6">Esta es tu página de Dashboard 🔐</p>

      <button
        onClick={logout}
        className="px-5 py-2 bg-[#d4af37] text-white rounded-lg hover:bg-[#bfa334] transition-all"
      >
        Cerrar sesión
      </button>
    </div>
  );
}
