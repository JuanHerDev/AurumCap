const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";

function authHeaders() {
    const token = typeof window !== "undefined" ? localStorage.getItem("aurum_access_token") : null;
  
    console.log("TOKEN ENVIADO AL BACKEND:", token); // <-- debug
  
    return token
      ? { Authorization: `Bearer ${token}` }
      : {};
  }

async function handleResponse(res: Response) {
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error((data && data.detail) || res.statusText || "Error");
    // @ts-ignore
    err.status = res.status;
    throw err;
  }
  return data;
}

export async function getSummary(): Promise<any> {
  const res = await fetch(`${baseUrl}/investments/summary`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(authHeaders() || {}),
    },
    credentials: "include",
  });
  return handleResponse(res);
}

export async function getInvestments(skip = 0, limit = 100): Promise<any[]> {
  const res = await fetch(`${baseUrl}/investments?skip=${skip}&limit=${limit}`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    credentials: "include",
  });
  return handleResponse(res);
}

export async function getInvestment(id: number): Promise<any> {
  const res = await fetch(`${baseUrl}/investments/${id}`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    credentials: "include",
  });
  return handleResponse(res);
}

export async function createInvestment(payload: any): Promise<any> {
  const res = await fetch(`${baseUrl}/investments`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  return handleResponse(res);
}

export async function updateInvestment(id: number, payload: any): Promise<any> {
  const res = await fetch(`${baseUrl}/investments/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  return handleResponse(res);
}

export async function deleteInvestment(id: number): Promise<null> {
  const res = await fetch(`${baseUrl}/investments/${id}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    credentials: "include",
  });
  return handleResponse(res);
}
