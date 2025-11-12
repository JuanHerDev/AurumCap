"use client";

import React from "react";

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-6">
      {children}
    </section>
  );
}
