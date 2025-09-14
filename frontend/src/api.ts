import type { Account, AccountDetails, Page } from "./types";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function listAccounts(): Promise<Account[]> {
  const r = await fetch(`${API_BASE}/accounts/`);
  if (!r.ok) throw new Error(`listAccounts ${r.status}`);
  return r.json();
}

export async function getAccount(id: string): Promise<AccountDetails> {
  const r = await fetch(`${API_BASE}/accounts/${encodeURIComponent(id)}`);
  if (!r.ok) throw new Error(`getAccount ${r.status}`);
  return r.json();
}

export async function disconnectAccount(id: string): Promise<void> {
  const r = await fetch(`${API_BASE}/accounts/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (!r.ok) throw new Error(`disconnectAccount ${r.status}`);
}

export async function fetchPage<T>(path: string, params: Record<string, any> = {}): Promise<Page<T>> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    qs.set(k, String(v));
  });
  const url = `${API_BASE}${path}${qs.toString() ? `?${qs}` : ""}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}
