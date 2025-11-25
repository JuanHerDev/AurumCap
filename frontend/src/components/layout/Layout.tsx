// components/Layout.tsx
"use client";

import React from "react";
import Navbar from "./Navbar";

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      {/* Main content con padding bottom solo para mobile */}
      <main className="pb-16 md:pb-0">
        {children}
      </main>
    </div>
  );
}