"use client";

import React from "react";
import AuthForm from "@/features/auth/components/AuthForm";

export default function LoginPage() {
    return (
        <main className="flex flex-col justify-center min-h-screen px-6 bg-white">
            <div className="max-w-md mx-auto w-full text-center">
                <h1 className="text-3xl font-bold mb-2 text-yellow-500">AurumCap</h1>
                <p className="text-gray-500 mb-4">Bienvenido de nuevo</p>
                <AuthForm mode="login" />
            </div>
        </main>
    );
}