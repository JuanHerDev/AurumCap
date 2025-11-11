"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setAccessToken } from "@/lib/api";

export default function OAuthSuccessPage() {
    const router = useRouter();
    const params = useSearchParams();

    useEffect(() => {
        const access = params.get("access_token");

        if (access) {
            setAccessToken(access);
            router.push("/dashboard");
        } else {
            router.push("/login");
        }
    }, []);

    return <p>Redireccionando...</p>
}