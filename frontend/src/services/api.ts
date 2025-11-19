const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Función helper para obtener token
function getToken() {
  // Por ejemplo, lo guardas en localStorage
  return localStorage.getItem("access_token");
}

async function fetchJSON(url: string, opts: RequestInit = {}) {
  const token = getToken();

  const headers = new Headers(opts.headers);
  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(url, {
    ...opts,
    headers,
    credentials: "include", // si también usas cookies
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }

  return res.json();
}

export async function getPortfolioSummary(): Promise<any> {
  return fetchJSON(`${API_BASE}/investments/summary`);
}

export async function getInvestments(): Promise<any> {
  return fetchJSON(`${API_BASE}/investments`);
}
