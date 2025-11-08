"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, registerSchema } from "@/features/auth/validations/authSchemas";
import { z } from "zod";
import { loginRequest, registerRequest } from "@/features/auth/services/auth.service";
import { useRouter } from "next/navigation";
import GoogleButton from "@/features/auth/components/GoogleButton";

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
        <form 
            onSubmit={handleSubmit(onSubmit)}
            className="flex flex-col gap-4 mt-6 w-full"    
        >
            <div>
                <label className="block text-sm font-medium text-gray-700">Correo</label>
                <input 
                    type="email" 
                    {...register("email")}
                    className="w-full p-3 border rounded-lg focus:ring focus:ring-yellow-200 outline-none"
                    placeholder="tucorreo@gmail.com"
                />
                {errors.email && (
                    <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
                )}
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Contraseña
                </label>
                <input 
                    type="password" 
                    {...register("password")}
                    className="w-full p-3 border rounded-lg focus:ring focus:ring-yellow-200 outline-none"
                    placeholder="******"
                />
                {errors.password && (
                    <p className="text-red-500 text-sm mt-1">
                        {errors.password.message}
                    </p>
                )}
            </div>

            {mode === "register" && (
                <div>
                    <label className="block text-sm font-medium text-gray-700">
                        Confirmar contraseña
                    </label>
                    <input 
                        type="password"
                        {...register("confirmPassword")}
                        className="w-full p-3 border rounded-lg focus:ring focus:ring-yellow-200 outline-none" 
                        placeholder="******"
                    />
                    {errors.confirmPassword && (
                        <p className="text-red-500 text-sm mt-1">
                            {errors.confirmPassword.message}
                        </p>
                    )}
                </div>
            )}

            <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-yellow-400 hover:bg-yellow-500 text-black py-3 rounded-lg font-semibold transition-all"
            >
                {isSubmitting
                    ? "Provessando..."
                    : mode === "login"
                    ? "Iniciar sesión"
                    : "Registrarse"}
            </button>

            <GoogleButton />

            {mode === "login" ? (
                <p className="text-sm text-gray-500 text-center">
                    ¿No tienes cuenta? {" "}
                    <a href="/register" className="text-yellow-600 font-semibold">
                        Regístrate
                    </a>
                </p>
            ) : (
                <p className="text-sm text-gray-500 text-center">
                    ¿Ya tienes cuenta? {" "}
                    <a href="/login" className="text-yellow-600 font-semibold">
                        Inicia sesión
                    </a>
                </p>
            )}
        </form>
    );
}