"use client";

import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Espera a que loading sea false
    if (!loading && !user && pathname !== "/login") {
      router.replace("/login"); // usar replace evita el "back" al dashboard
    }
  }, [loading, user, router, pathname]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500 text-sm">Cargando...</p>
      </div>
    );
  }

  // Solo renderiza children si hay user
  if (!user) return null;

  return <div className="min-h-screen bg-gray-50">{children}</div>;
}
