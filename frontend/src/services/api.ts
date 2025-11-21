import api from "@/lib/api";

/**
 * Obtiene el resumen del portafolio del usuario.
 */
export async function getPortfolioSummary() {
  const res = await api.get("/investments/summary");
  return res.data;
}

/**
 * Obtiene todos los investments.
 */
export async function getInvestments() {
  const res = await api.get("/investments");
  return res.data;
}

/**
 * Crea una nueva inversión.
 */
export async function createInvestment(data: any) {
  const res = await api.post("/investments", data);
  return res.data;
}

/**
 * Actualiza una inversión por ID.
 */
export async function updateInvestment(id: number, data: any) {
  const res = await api.put(`/investments/${id}`, data);
  return res.data;
}

/**
 * Elimina una inversión por ID.
 */
export async function deleteInvestment(id: number) {
  const res = await api.delete(`/investments/${id}`);
  return res.data;
}
