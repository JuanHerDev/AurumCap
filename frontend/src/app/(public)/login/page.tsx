"use client";

import React from "react";
import AuthForm from "@/features/auth/components/AuthForm";
import AuthLayout from "@/features/auth/components/AuthLayout";

export default function LoginPage() {
    return (
        <AuthLayout
            title="Bienvenido de nuevo"
            subtitle="Accede a tu portafolio de inversión"
            sideImage="login-ilustration.svg"
            imagePosition="left"
        >
            <AuthForm mode="login" />
        </AuthLayout>
    );
}