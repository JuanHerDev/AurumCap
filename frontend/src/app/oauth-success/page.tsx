"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { setAccessToken } from "@/lib/api";

export default function OAuthSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();

  useEffect(() => {
    const token = searchParams.get("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    // Guardar token globalmente
    setAccessToken(token);

    refreshUser()
      .then(() => router.push("/dashboard"))
      .catch(() => router.push("/login"));
  }, [searchParams, router, refreshUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-700">
          Procesando tu inicio de sesión...
        </h2>
        <p className="text-sm text-gray-500 mt-2">
          Esto tomará solo un momento.
        </p>
      </div>
    </div>
  );
}
