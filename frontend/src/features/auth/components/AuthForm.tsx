"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, registerSchema } from "@/features/auth/validations/authSchemas";
import { z } from "zod";
import { loginRequest, registerRequest } from "@/features/auth/services/auth.service";
import { useRouter } from "next/navigation";
import GoogleButton from "@/features/auth/components/GoogleButton";
import { Eye, EyeOff, Mail, Lock } from "lucide-react";

type Mode = "login" | "register";

interface Props {
  mode: Mode;
}

export default function AuthForm({ mode }: Props) {
  const router = useRouter();
  const schema = mode === "login" ? loginSchema : registerSchema;

  type FormValues = z.infer<typeof loginSchema> & Partial<z.infer<typeof registerSchema>>;
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const onSubmit = async (data: any) => {
    try {
      if (mode === "login") {
        await loginRequest(data.email, data.password);
        router.push("/dashboard");
      } else {
        await registerRequest(data.email, data.password);
        router.push("/login");
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Error al procesar la solicitud");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 w-full">
      {/* Email */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">Correo electrónico</label>
        <div className="relative">
          <Mail className="absolute left-3 top-3.5 text-gray-400 w-5 h-5" />
          <input
            type="email"
            {...register("email")}
            placeholder="tu.correo@ejemplo.com"
            className="w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-yellow-300 transition text-sm"
          />
        </div>
        {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
      </div>

      {/* Password */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
        <div className="relative">
          <Lock className="absolute left-3 top-3.5 text-gray-400 w-5 h-5" />
          <input
            type={showPassword ? "text" : "password"}
            {...register("password")}
            placeholder="Ingresa tu contraseña"
            className="w-full pl-10 pr-10 py-3 border border-gray-200 rounded-xl shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-yellow-300 transition text-sm"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600"
            aria-label="mostrar contraseña"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
      </div>

      {/* Confirm Password (register) */}
      {mode === "register" && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar contraseña</label>
          <div className="relative">
            <Lock className="absolute left-3 top-3.5 text-gray-400 w-5 h-5" />
            <input
              type={showConfirm ? "text" : "password"}
              {...register("confirmPassword")}
              placeholder="Confirma tu contraseña"
              className="w-full pl-10 pr-10 py-3 border border-gray-200 rounded-xl shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-yellow-300 transition text-sm"
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600"
              aria-label="mostrar confirmar contraseña"
            >
              {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {errors.confirmPassword && <p className="text-red-500 text-xs mt-1">{errors.confirmPassword.message}</p>}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-[#d4af37] hover:bg-[#c09c32] active:scale-95 text-white font-semibold py-3 rounded-xl transition-all shadow-sm"
      >
        {isSubmitting ? "Procesando..." : mode === "login" ? "Iniciar sesión" : "Registrarme"}
      </button>

      {/* Divider */}
      <div className="flex items-center justify-center gap-2 my-2">
        <div className="h-px bg-gray-300 w-1/3" />
        <span className="text-gray-500 text-sm">O continúa con</span>
        <div className="h-px bg-gray-300 w-1/3" />
      </div>

      {/* Google */}
      <GoogleButton />

      {/* Toggle */}
      {mode === "login" ? (
        <p className="text-sm text-gray-500 text-center mt-3">
          ¿No tienes cuenta?{" "}
          <a href="/register" className="text-[#d4af37] font-semibold hover:underline">
            Regístrate
          </a>
        </p>
      ) : (
        <p className="text-sm text-gray-500 text-center mt-3">
          ¿Ya tienes cuenta?{" "}
          <a href="/login" className="text-[#d4af37] font-semibold hover:underline">
            Inicia sesión
          </a>
        </p>
      )}
    </form>
  );
}
