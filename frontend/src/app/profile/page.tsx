// app/profile/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";
import { 
  FaUser, 
  FaLock, 
  FaShieldAlt, 
  FaSignOutAlt,
  FaArrowLeft,
  FaEdit
} from "react-icons/fa";
import ChangePassword from "@/components/profile/ChangePassword";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [activeSection, setActiveSection] = useState<'main' | 'security' | 'change-password'>('main');
  const [isRedirecting, setIsRedirecting] = useState(false);

  // Usar useEffect para redirecciones
  useEffect(() => {
    if (!user && !isRedirecting) {
      setIsRedirecting(true);
      router.push('/login');
    }
  }, [user, isRedirecting, router]);

  // Mostrar loading mientras se verifica la autenticación
  if (!user || isRedirecting) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#B59F50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 text-sm">Cargando...</p>
        </div>
      </div>
    );
  }

  if (activeSection === 'security') {
    return <SecuritySettings onBack={() => setActiveSection('main')} />;
  }

  if (activeSection === 'change-password') {
    return <ChangePassword onBack={() => setActiveSection('main')} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-4 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Perfil</h1>
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <FaArrowLeft size={16} />
              <span>Volver</span>
            </button>
          </div>

          {/* User Info Card */}
          <div className="bg-linear-to-r from-[#B59F50] to-[#A68F45] rounded-xl p-6 text-white mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <FaUser size={24} />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold">{user.full_name || 'Usuario'}</h2>
                <p className="text-white/80">{user.email}</p>
                <span className="inline-block mt-2 px-3 py-1 bg-white/20 rounded-full text-sm">
                  Inversor Principiante
                </span>
              </div>
              <button className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors">
                <FaEdit size={16} />
              </button>
            </div>
          </div>

          {/* Options Grid */}
          <div className="space-y-3">
            <ProfileOption
              icon={FaLock}
              title="Cambiar contraseña"
              description="Actualiza tu contraseña de acceso"
              onClick={() => setActiveSection('change-password')}
            />
            
            <ProfileOption
              icon={FaShieldAlt}
              title="Seguridad"
              description="Configuración de seguridad y sesiones"
              onClick={() => setActiveSection('security')}
            />
            
            <ProfileOption
              icon={FaSignOutAlt}
              title="Cerrar sesión"
              description="Salir de tu cuenta"
              onClick={logout}
              isDestructive
            />
          </div>
        </div>

        {/* Stats Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Estadísticas</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-[#B59F50]">5</div>
              <div className="text-sm text-gray-500">Inversiones</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[#B59F50]">12.5%</div>
              <div className="text-sm text-gray-500">Rendimiento</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[#B59F50]">3</div>
              <div className="text-sm text-gray-500">Meses</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[#B59F50]">Bajo</div>
              <div className="text-sm text-gray-500">Riesgo</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Componente para las opciones del perfil
const ProfileOption = ({ 
  icon: Icon, 
  title, 
  description, 
  onClick, 
  isDestructive = false 
}: {
  icon: any;
  title: string;
  description: string;
  onClick: () => void;
  isDestructive?: boolean;
}) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all duration-200 ${
      isDestructive
        ? 'border-red-200 bg-red-50 hover:bg-red-100 text-red-700'
        : 'border-gray-200 bg-gray-50 hover:bg-gray-100 text-gray-700'
    }`}
  >
    <div className={`p-3 rounded-lg ${
      isDestructive ? 'bg-red-100' : 'bg-[#B59F50]'
    }`}>
      <Icon size={20} className={isDestructive ? 'text-red-600' : 'text-white'} />
    </div>
    <div className="flex-1 text-left">
      <div className={`font-semibold ${isDestructive ? 'text-red-800' : 'text-gray-900'}`}>
        {title}
      </div>
      <div className={`text-sm ${isDestructive ? 'text-red-600' : 'text-gray-500'}`}>
        {description}
      </div>
    </div>
  </button>
);

// Componente para configuración de seguridad
const SecuritySettings = ({ onBack }: { onBack: () => void }) => {
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 pt-4 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <FaArrowLeft size={16} />
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Configuración de Seguridad</h1>
          </div>

          {/* Two Factor Authentication */}
          <div className="mb-6">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FaShieldAlt className="text-blue-600" size={20} />
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Autenticación de dos factores</div>
                  <div className="text-sm text-gray-500">Añade una capa extra de seguridad a tu cuenta</div>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={twoFactorEnabled}
                  onChange={(e) => setTwoFactorEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#B59F50]"></div>
              </label>
            </div>
          </div>

          {/* Session Management */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Gestión de Sesiones</h3>
            
            <button className="w-full flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <FaUser className="text-green-600" size={16} />
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Ver sesiones activas</div>
                  <div className="text-sm text-gray-500">Revisa los dispositivos conectados</div>
                </div>
              </div>
            </button>

            <button className="w-full flex items-center justify-between p-4 border border-red-200 bg-red-50 rounded-xl hover:bg-red-100 transition-colors">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 rounded-lg">
                  <FaSignOutAlt className="text-red-600" size={16} />
                </div>
                <div>
                  <div className="font-semibold text-red-800">Cerrar todas las sesiones</div>
                  <div className="text-sm text-red-600">Desconecta todos los dispositivos excepto este</div>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};