// components/Navbar.tsx
"use client";

import React from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter, usePathname } from "next/navigation";
import { 
  FaHome, 
  FaBriefcase, 
  FaChartLine, 
  FaUser,
  FaSignOutAlt 
} from "react-icons/fa";

export default function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // 🚨 Si NO hay usuario, no mostrar la navbar
  if (!user) return null;

  const navigationItems = [
    { path: '/dashboard', label: 'Inicio', icon: FaHome },
    { path: '/portfolio', label: 'Portafolio', icon: FaBriefcase },
    { path: '/simulator', label: 'Simulador', icon: FaChartLine },
    { path: '/profile', label: 'Perfil', icon: FaUser },
  ];

  // Determinar si estamos en una página principal
  const isMainPage = ['/dashboard', '/portfolio', '/simulator', '/profile'].includes(pathname);

  // Función para redirigir a la landing page
  const handleLogoClick = () => {
    router.push('/');
  };

  return (
    <>
      {/* Top Navbar - Visible en todos los dispositivos */}
      <nav className="flex items-center justify-between p-4 bg-[#B59F50] text-white shadow-md">
        {/* Logo - Ahora es clickable */}
        <button
          onClick={handleLogoClick}
          className="font-bold text-2xl text-white drop-shadow-md hover:opacity-80 transition-opacity duration-200 cursor-pointer"
        >
          AurumCap
        </button>

        {/* Desktop Navigation - Solo visible en md+ */}
        <div className="hidden md:flex items-center gap-6">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                  isActive 
                    ? 'bg-white/20 text-white' 
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon size={18} />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* User Info and Logout */}
        <div className="flex items-center gap-4">
          <div className="text-sm hidden sm:block">
            <div className="font-semibold">{user.full_name || 'Usuario'}</div>
            <div className="text-white/80 text-xs">{user.email}</div>
          </div>
          
          <button
            onClick={() => logout()}
            className="flex items-center gap-2 bg-white/20 hover:bg-white/30 px-3 py-2 rounded-lg transition-all duration-200 text-sm"
          >
            <FaSignOutAlt size={14} />
            <span className="hidden sm:block">Salir</span>
          </button>
        </div>
      </nav>

      {/* Bottom Navigation - Solo visible en mobile (md-) y solo en páginas principales */}
      {isMainPage && (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-3 px-6 z-40 md:hidden">
          <div className="flex justify-between items-center">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              
              return (
                <button
                  key={item.path}
                  onClick={() => router.push(item.path)}
                  className={`flex flex-col items-center gap-1 transition-colors ${
                    isActive 
                      ? 'text-[#B59F50]' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon size={20} />
                  <span className="text-xs font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </>
  );
}