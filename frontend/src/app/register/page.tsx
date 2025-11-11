"use client";

import React from "react";
import AuthForm from "@/features/auth/components/AuthForm";
import AuthLayout from "@/features/auth/components/AuthLayout";


export default function RegisterPage() {
    return (
      <AuthLayout
        title="Crea tu cuenta"
        subtitle="Maneja tus inversiones. simple, claro y concreto."
        sideImage="/register-ilustration.svg"
        imagePosition="right"
      >
        <AuthForm mode="register" />
      </AuthLayout>
    );
}