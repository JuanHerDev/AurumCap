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

// Investment endpoints
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

// Platform endpoints - NUEVOS
export async function getPlatforms(assetType?: string): Promise<any[]> {
  const url = assetType 
    ? `${baseUrl}/investments/platforms/list?asset_type=${assetType}`
    : `${baseUrl}/investments/platforms/list`;
  
  console.log(`🔍 Fetching platforms from: ${url}`);
  
  const res = await ApiInterceptor.fetchWithAuth(url);
  const platforms = await handleResponse(res);
  
  console.log(`✅ Found ${platforms.length} platforms`);
  return platforms;
}

export async function getPlatformsByAssetType(assetType: string): Promise<any[]> {
  const res = await ApiInterceptor.fetchWithAuth(
    `${baseUrl}/platforms/by-asset-type/${assetType}?active_only=true`
  );
  return handleResponse(res);
}

export async function getAllPlatforms(): Promise<any[]> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/platforms?active_only=true`);
  return handleResponse(res);
}

// Strategy endpoints - NUEVOS
export async function getStrategies(): Promise<any[]> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/strategies/list`);
  return handleResponse(res);
}

// Portfolio analytics endpoints
export async function getAggregatedHoldings(): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/aggregated`);
  return handleResponse(res);
}

export async function getPortfolioMetrics(): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/summary`);
  return handleResponse(res);
}

// Debug endpoints
export async function debugUserHoldings(): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/debug/user-holdings`);
  return handleResponse(res);
}

// Test endpoints
export async function testCreateSimple(): Promise<any> {
  const res = await ApiInterceptor.fetchWithAuth(`${baseUrl}/investments/test-simple`, {
    method: "POST",
  });
  return handleResponse(res);
}

// Utility function para formatear payload de inversión
export async function formatInvestmentPayload(formData: any) {
  const {
    symbol,
    asset_name,
    asset_type,
    quantity,
    purchase_price,
    invested_amount,
    currency,
    platform,
    strategy,
    transaction_date,
    notes
  } = formData;

  // Buscar el platform_id basado en el nombre de la plataforma
  // Esto asume que tienes una manera de mapear nombres de plataforma a IDs
  // Por ahora, usaremos null y el backend manejará la plataforma por nombre
  const platform_id = platform ? await getPlatformIdByName(platform) : null;

  return {
    symbol: symbol.toUpperCase(),
    asset_name: asset_name || symbol.toUpperCase(),
    asset_type: asset_type,
    quantity: parseFloat(quantity),
    purchase_price: parseFloat(purchase_price),
    invested_amount: parseFloat(invested_amount),
    currency: currency,
    platform_id: platform_id,
    platform_specific_id: null, // Puedes ajustar esto según necesites
    strategy: strategy || null,
    transaction_date: transaction_date ? new Date(transaction_date).toISOString() : new Date().toISOString(),
    notes: notes || null
  };
}

// Función auxiliar para obtener platform_id por nombre
async function getPlatformIdByName(platformName: string): Promise<number | null> {
  try {
    const platforms = await getPlatforms();
    const platform = platforms.find((p: any) => p.value === platformName || p.name === platformName);
    return platform ? platform.id : null;
  } catch (error) {
    console.error('Error getting platform ID:', error);
    return null;
  }
}

// Función para validar datos del formulario antes de enviar
export function validateInvestmentForm(formData: any): string[] {
  const errors: string[] = [];

  if (!formData.symbol?.trim()) {
    errors.push("El símbolo es requerido");
  }

  if (!formData.asset_type) {
    errors.push("El tipo de activo es requerido");
  }

  if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
    errors.push("La cantidad debe ser mayor a 0");
  }

  if (!formData.purchase_price || parseFloat(formData.purchase_price) <= 0) {
    errors.push("El precio de compra debe ser mayor a 0");
  }

  if (!formData.invested_amount || parseFloat(formData.invested_amount) <= 0) {
    errors.push("El monto invertido debe ser mayor a 0");
  }

  if (!formData.currency) {
    errors.push("La moneda es requerida");
  }

  if (!formData.platform) {
    errors.push("La plataforma es requerida");
  }

  // Validar consistencia entre cantidad, precio y monto invertido
  const quantity = parseFloat(formData.quantity);
  const purchasePrice = parseFloat(formData.purchase_price);
  const investedAmount = parseFloat(formData.invested_amount);
  const calculatedAmount = quantity * purchasePrice;

  if (Math.abs(calculatedAmount - investedAmount) > 0.01) {
    errors.push(`El monto invertido (${investedAmount}) no coincide con cantidad × precio (${calculatedAmount.toFixed(2)})`);
  }

  return errors;
}

// Función para calcular automáticamente el monto invertido
export function calculateInvestedAmount(quantity: string, purchasePrice: string): number {
  const qty = parseFloat(quantity) || 0;
  const price = parseFloat(purchasePrice) || 0;
  return qty * price;
}

// Exportar todas las funciones
export const portfolioService = {
  // Investments
  createInvestment,
  getSummary,
  getInvestments,
  getInvestment,
  updateInvestment,
  deleteInvestment,
  
  // Platforms
  getPlatforms,
  getPlatformsByAssetType,
  getAllPlatforms,
  
  // Strategies
  getStrategies,
  
  // Analytics
  getAggregatedHoldings,
  getPortfolioMetrics,
  
  // Debug & Test
  debugUserHoldings,
  testCreateSimple,
  
  // Utilities
  formatInvestmentPayload,
  validateInvestmentForm,
  calculateInvestedAmount
};

export default portfolioService;