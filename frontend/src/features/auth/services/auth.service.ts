import api, { setAccessToken } from "@/lib/api";

export type LoginResponse = { access_token: string; token_type: string };

export async function loginRequest(email: string, password: string) {
    const res = await api.post<LoginResponse>("/auth/login", { email, password });
    const token = res.data?.access_token;

    if (token) setAccessToken(token); // Store in sessionStorage
    return res.data;
}

export async function registerRequest(email: string, password: string, full_name?: string) {
    const res = await api.post<LoginResponse>("/auth/register", { email, password, full_name });
    const token = res.data?.access_token;

    if (token) setAccessToken(token);
    return res.data;
}

export async function logoutRequest() {
    // Backend: Revoke refresh tokend & clear cookie
    await api.post("/auth/logout");
    setAccessToken(null);
}

export async function meRequest() {
    const token = localStorage.getItem("access_token");
    if (!token) throw new Error("No token found");

    const res = await fetch("http://localhost:8000/auth/me", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        credentials: "include",
    });

    if (!res.ok) {
        throw new Error(`Error fetching user: ${res.status}`)
    }

    return await res.json();
}