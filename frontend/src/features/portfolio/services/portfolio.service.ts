// src/features/portfolio/services/portfolio.service.ts
import { AuthService } from "@/services/auth.service";
import { ApiInterceptor } from "@/services/api.interceptor";

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";

async function handleResponse(res: Response) {
  console.log(`📊 Response status: ${res.status} for ${res.url}`);
  
  if (res.status === 204) return null;
  
  const data = await res.json().catch(() => null);
  console.log(`📊 Response data:`, data);
  
  if (!res.ok) {
    // Mejorar el manejo de errores para mostrar más detalles
    let errorMessage = "Error del servidor";
    
    if (data) {
      if (typeof data.detail === 'string') {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        // Si es un array de errores de validación de Pydantic
        errorMessage = data.detail.map((err: any) => {
          const field = err.loc?.join('.') || 'campo';
          return `${field}: ${err.msg}`;
        }).join(', ');
      } else if (data.detail && typeof data.detail === 'object') {
        errorMessage = JSON.stringify(data.detail);
      } else if (data.message) {
        errorMessage = data.message;
      } else if (Array.isArray(data)) {
        errorMessage = data.map((err: any) => 
          `${err.loc?.join('.')}: ${err.msg}`
        ).join(', ');
      } else {
        errorMessage = `Error ${res.status}: ${JSON.stringify(data)}`;
      }
    } else {
      errorMessage = res.statusText || `Error ${res.status}`;
    }
    
    console.error(`❌ Error en la respuesta:`, errorMessage);
    const err = new Error(errorMessage);
    (err as any).status = res.status;
    (err as any).responseData = data; // Guardar datos de respuesta para debug
    throw err;
  }
  
  return data;
}

export async function createInvestment(payload: any): Promise<any> {
  console.log("📤 Enviando payload a /investments:", JSON.stringify(payload, null, 2));
  
  // Validar y redondear números antes de enviar
  const validatedPayload = {
    ...payload,
    invested_amount: parseFloat(payload.invested_amount.toFixed(2)),
    quantity: parseFloat(payload.quantity.toFixed(6)),
    purchase_price: parseFloat(payload.purchase_price.toFixed(6)),
  };
  
  console.log("📤 Payload validado:", JSON.stringify(validatedPayload, null, 2));
  
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments`, {
    method: "POST",
    body: JSON.stringify(validatedPayload),
  });
  
  return handleResponse(res);
}

export async function getSummary(): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/summary`);
  return handleResponse(res);
}

export async function getInvestments(skip = 0, limit = 100): Promise<any[]> {
  const res = await ApiInterceptor.fetchWithAuth(
    `${baseUrl}/investments?skip=${skip}&limit=${limit}`
  );
  return handleResponse(res);
}

export async function getInvestment(id: number): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/${id}`);
  return handleResponse(res);
}

export async function updateInvestment(id: number, payload: any): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function deleteInvestment(id: number): Promise<null> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/${id}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}

// Función específica para cargar plataformas por tipo de activo
export async function getPlatformsByAssetType(assetType: string): Promise<any[]> {
  const res = await ApiInterceptor.fetchWithAuth(
    `${baseUrl}/platforms/by-asset-type/${assetType}?active_only=true`
  );
  return handleResponse(res);
}