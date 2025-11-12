"use client";

import React from "react";

export default function AuthLayout({
  children,
  sideImage = "/register-ilustration.svg",
  title,
  subtitle,
  imagePosition = "right",
}: {
  children: React.ReactNode;
  sideImage?: string;
  title: string;
  subtitle?: string;
  imagePosition?: "left" | "right";
}) {
  return (
    <main className="min-h-screen w-full flex flex-col md:flex-row bg-gray-50">
      {/* IMAGE LEFT (desktop) */}
      {imagePosition === "left" && (
        <section className="hidden md:flex w-1/2 items-center justify-center bg-white border-r border-gray-200">
          <img
            src={sideImage}
            alt="Auth illustration"
            className="w-3/4 max-w-lg object-contain"
          />
        </section>
      )}

      {/* FORM AREA */}
      <section className="w-full md:w-1/2 flex items-center justify-center px-6 md:px-12 py-12">
        {/* Card centrada con max width */}
        <div className="w-full max-w-md bg-white rounded-2xl shadow-md p-8 md:p-10">
          {/* MOBILE HEADER */}
          <div className="md:hidden mb-4 text-center">
            <h1 className="text-2xl md:text-3xl font-bold text-[#d4af37]">{title}</h1>
            {subtitle && <p className="text-gray-600 text-sm mt-1">{subtitle}</p>}
          </div>

          {/* DESKTOP HEADER */}
          <div className="hidden md:block mb-6 text-left">
            <h1 className="text-3xl md:text-4xl font-bold text-[#d4af37]">{title}</h1>
            {subtitle && <p className="text-gray-500 mt-2">{subtitle}</p>}
          </div>

          {/* CONTENT (form) */}
          <div>{children}</div>
        </div>
      </section>

      {/* IMAGE RIGHT (desktop) */}
      {imagePosition === "right" && (
        <section className="hidden md:flex w-1/2 items-center justify-center bg-white border-l border-gray-200">
          <img
            src={sideImage}
            alt="Auth illustration"
            className="w-3/4 max-w-xl object-contain"
          />
        </section>
      )}
    </main>
  );
}
