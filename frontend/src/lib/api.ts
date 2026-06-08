import type { SearchParams, SearchResponse, Supplier, Category } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export async function searchSuppliers(params: SearchParams): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/api/search", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getCategories(): Promise<Category[]> {
  return apiFetch<Category[]>("/api/suppliers/categories");
}

export async function getRegions(): Promise<string[]> {
  return apiFetch<string[]>("/api/suppliers/regions");
}

export async function getSupplier(id: number): Promise<Supplier> {
  return apiFetch<Supplier>(`/api/suppliers/${id}`);
}
