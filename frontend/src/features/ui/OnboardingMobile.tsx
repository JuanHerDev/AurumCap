"use client";

import React from "react";

export default function OnboardingMobile() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center px-6 py-8">
      <div className="w-full max-w-md">
        <img src="/mobile-hero.svg" alt="Hero" className="w-full rounded-2xl shadow-card"/>
        <div className="grid grid-cols-2 gap-3 mt-6">
          <button className="flex flex-col items-center gap-2 bg-white rounded-xl p-4 shadow-card">
            <div className="w-10 h-10 rounded-lg bg-aurum-100 flex items-center justify-center text-aurum-500">📘</div>
            <span className="text-sm font-semibold">Aprende</span>
          </button>
          <button className="flex flex-col items-center gap-2 bg-white rounded-xl p-4 shadow-card">
            <div className="w-10 h-10 rounded-lg bg-aurum-100 flex items-center justify-center text-aurum-500">$</div>
            <span className="text-sm font-semibold">Invierte</span>
          </button>
        </div>

        <div className="mt-4 bg-white p-4 rounded-xl shadow-card text-center">
          <div className="text-sm text-gray-600">Crecimiento</div>
        </div>

        <button className="w-full mt-6 bg-aurum-500 text-white py-3 rounded-xl2 font-semibold">Crear cuenta</button>
        <button className="w-full mt-3 border border-aurum-300 text-aurumText py-3 rounded-xl2 font-medium bg-white">Iniciar sesión</button>

        <div className="flex justify-between text-xs text-gray-500 mt-6">
          <a href="/privacy">Política de Privacidad</a>
          <a href="/support">Soporte</a>
        </div>
      </div>
    </div>
  );
}
