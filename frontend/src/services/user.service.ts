// features/auth/services/userService.ts
import { api } from '@/services/api';

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

export interface UserUpdateData {
  full_name?: string;
  picture_url?: string;
}

export const userService = {
  async changePassword(passwordData: ChangePasswordData): Promise<{ message: string; detail: string }> {
    try {
      const response = await api.put('/auth/me/password', passwordData);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al cambiar la contraseña');
    }
  },

  async getCurrentUser() {
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al obtener información del usuario');
    }
  },

  async updateUser(userData: UserUpdateData) {
    try {
      const response = await api.put('/users/me', userData);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Error al actualizar la información del usuario');
    }
  }
};