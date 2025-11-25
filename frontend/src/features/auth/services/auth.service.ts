import api, { setAccessToken } from "@/lib/api";

export type LoginResponse = { access_token: string; token_type: string };

export async function loginRequest(email: string, password: string) {
    const res = await api.post<LoginResponse>("/auth/login", { email, password });

    console.log("LOGIN RESPONSE:", res.data);

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
  const res = await api.get("/auth/me");
  return res.data;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

export interface UserUpdateData {
  full_name?: string;
  picture_url?: string;
}

/**
 * Cambia la contraseña del usuario actual
 */
export async function changePasswordRequest(passwordData: ChangePasswordData): Promise<{ message: string; detail: string }> {
  try {
    const res = await api.put("/auth/me/password", passwordData);
    return res.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Error al cambiar la contraseña';
    throw new Error(errorMessage);
  }
}

/**
 * Obtiene la información del usuario actual
 */
export async function getCurrentUserRequest() {
  try {
    const res = await api.get("/users/me");
    return res.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Error al obtener información del usuario';
    throw new Error(errorMessage);
  }
}

/**
 * Actualiza la información del usuario actual
 */
export async function updateUserRequest(userData: UserUpdateData) {
  try {
    const res = await api.put("/users/me", userData);
    return res.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Error al actualizar la información del usuario';
    throw new Error(errorMessage);
  }
}