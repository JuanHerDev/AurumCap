"use client";

import React, { useEffect } from "react";
import { useAuth } from "@/features/auth/context/AuthProvider";
import { useRouter } from "next/navigation";

export default function PrivateLayout({ children }: { children: React.ReactNode }) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !user) {
            // If not authenticated, redirect to login page
            router.push("/login");
        }
    }, [user, loading, router]);

    
    if (loading || !user) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <p className="text-gray-500 text-lg">Loading...</p>
            </div>
        );
    }

    return <>{children}</>
}