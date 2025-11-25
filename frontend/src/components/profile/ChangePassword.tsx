// components/profile/ChangePassword.tsx
"use client";

import React, { useState } from "react";
import { FaArrowLeft, FaEye, FaEyeSlash, FaCheck, FaTimes } from "react-icons/fa";
import { useAuth } from "@/features/auth/context/AuthProvider";

export default function ChangePassword({ onBack }: { onBack: () => void }) {
  const { changePassword } = useAuth();
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    // Validaciones del frontend
    if (formData.new_password !== formData.confirm_password) {
      setMessage({ type: 'error', text: 'Las contraseñas nuevas no coinciden' });
      setLoading(false);
      return;
    }

    if (formData.new_password.length < 8) {
      setMessage({ type: 'error', text: 'La nueva contraseña debe tener al menos 8 caracteres' });
      setLoading(false);
      return;
    }

    try {
      // Usar la función del contexto de autenticación
      await changePassword(formData.current_password, formData.new_password);
      
      setMessage({ 
        type: 'success', 
        text: 'Contraseña cambiada exitosamente' 
      });
      
      // Limpiar formulario después de éxito
      setFormData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.message || 'Error al cambiar la contraseña' 
      });
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const passwordStrength = {
    hasMinLength: formData.new_password.length >= 8,
    hasUpperCase: /[A-Z]/.test(formData.new_password),
    hasLowerCase: /[a-z]/.test(formData.new_password),
    hasNumbers: /[0-9]/.test(formData.new_password),
    hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(formData.new_password),
  };

  const isPasswordStrong = Object.values(passwordStrength).every(Boolean);

  return (
    <div className="min-h-screen bg-gray-50 pt-4 px-4">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
              disabled={loading}
            >
              <FaArrowLeft size={16} />
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Cambiar Contraseña</h1>
          </div>

          {/* Mensaje de estado */}
          {message && (
            <div className={`mb-4 p-3 rounded-lg ${
              message.type === 'success' 
                ? 'bg-green-50 border border-green-200 text-green-800' 
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}>
              {message.text}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña actual
              </label>
              <div className="relative">
                <input
                  type={showPasswords.current ? "text" : "password"}
                  value={formData.current_password}
                  onChange={(e) => setFormData(prev => ({ ...prev, current_password: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('current')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  disabled={loading}
                >
                  {showPasswords.current ? <FaEyeSlash size={16} /> : <FaEye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nueva contraseña
              </label>
              <div className="relative">
                <input
                  type={showPasswords.new ? "text" : "password"}
                  value={formData.new_password}
                  onChange={(e) => setFormData(prev => ({ ...prev, new_password: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent"
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('new')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  disabled={loading}
                >
                  {showPasswords.new ? <FaEyeSlash size={16} /> : <FaEye size={16} />}
                </button>
              </div>

              {/* Indicador de fortaleza de contraseña */}
              {formData.new_password && (
                <div className="mt-2 space-y-1">
                  <div className="text-xs text-gray-600">La contraseña debe contener:</div>
                  <div className="space-y-1">
                    {Object.entries(passwordStrength).map(([key, isValid]) => (
                      <div key={key} className="flex items-center gap-2 text-xs">
                        {isValid ? (
                          <FaCheck className="text-green-500" size={10} />
                        ) : (
                          <FaTimes className="text-red-400" size={10} />
                        )}
                        <span className={isValid ? 'text-green-600' : 'text-gray-500'}>
                          {key === 'hasMinLength' && 'Mínimo 8 caracteres'}
                          {key === 'hasUpperCase' && 'Una letra mayúscula'}
                          {key === 'hasLowerCase' && 'Una letra minúscula'}
                          {key === 'hasNumbers' && 'Un número'}
                          {key === 'hasSpecialChar' && 'Un carácter especial'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirmar nueva contraseña
              </label>
              <div className="relative">
                <input
                  type={showPasswords.confirm ? "text" : "password"}
                  value={formData.confirm_password}
                  onChange={(e) => setFormData(prev => ({ ...prev, confirm_password: e.target.value }))}
                  className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-[#B59F50] focus:border-transparent ${
                    formData.confirm_password && formData.new_password !== formData.confirm_password
                      ? 'border-red-300'
                      : 'border-gray-300'
                  }`}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('confirm')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  disabled={loading}
                >
                  {showPasswords.confirm ? <FaEyeSlash size={16} /> : <FaEye size={16} />}
                </button>
              </div>
              {formData.confirm_password && formData.new_password !== formData.confirm_password && (
                <div className="text-red-500 text-xs mt-1">Las contraseñas no coinciden</div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !isPasswordStrong || formData.new_password !== formData.confirm_password}
              className="w-full bg-[#B59F50] text-white py-3 px-4 rounded-lg hover:bg-[#A68F45] transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Cambiando contraseña...' : 'Cambiar Contraseña'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}