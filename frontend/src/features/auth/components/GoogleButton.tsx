"use client";

import React from "react";

export default function GoogleButton() {
  const handleGoogleLogin = () => {
    try {
      window.location.href = `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/auth/oauth/google/login`;
    } catch (err) {
      console.error("Error iniciando sesión con Google:", err);
    }
  };

  return (
    <button
      type="button"
      onClick={handleGoogleLogin}
      className="w-full flex items-center justify-center text-gray-600 gap-3 border border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-all text-sm font-medium shadow-sm bg-white"
    >
      <img src="/google-icon.svg" alt="Google" className="w-5 h-5" />
      <span>Continuar con Google</span>
    </button>
  );
}
