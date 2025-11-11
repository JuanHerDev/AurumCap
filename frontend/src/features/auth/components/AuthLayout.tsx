"use client";

import React from "react";

export default function AuthLayout({
    children,
    sideImage = "/register-ilustration.svg",
    title,
    subtitle,
    imagePosition = "right", //"left" | "right"
} : {
    children: React.ReactNode;
    sideImage?: string;
    title: string;
    subtitle?: string;
    imagePosition?: "left" | "right";
}) {
    return (
        <main className="min-h-screen w-full flex flex-col md:flex-row bg-gray-50">

      {/* =========== DESKTOP: Image Left ============= */}
      {imagePosition === "left" && (
        <section className="
          hidden md:flex w-1/2 
          items-center justify-center bg-white
          border-r border-gray-200
        ">
          <img
            src={sideImage}
            alt="Auth illustration"
            className="w-3/4 max-w-lg object-contain"
          />
        </section>
      )}

      {/* =========== FORM AREA ============= */}
      <section className="
        w-full md:w-1/2 
        flex flex-col items-center justify-center
        px-6 py-10
      ">
        
        {/* MOBILE HEADER */}
        <div className="w-full text-center mb-8 md:hidden">
          <h1 className="text-3xl font-bold text-[#d4af37]">{title}</h1>
          {subtitle && (
            <p className="text-gray-600 text-sm mt-1">{subtitle}</p>
          )}
        </div>

        {/* CARD */}
        <div className="w-full max-w-sm bg-white rounded-2xl shadow-md p-8">
          <h1 className="hidden md:block text-3xl font-bold text-[#d4af37] mb-2">
            {title}
          </h1>
          {subtitle && (
            <p className="hidden md:block text-gray-500 mb-6">
              {subtitle}
            </p>
          )}

          {children}
        </div>
      </section>

      {/* =========== DESKTOP: Image Right ============= */}
      {imagePosition === "right" && (
        <section className="
          hidden md:flex w-1/2 
          items-center justify-center bg-white
          border-l border-gray-200
        ">
          <img
            src={sideImage}
            alt="Auth illustration"
            className="w-3/4 max-w-lg object-contain"
          />
        </section>
      )}
    </main>
    );
}