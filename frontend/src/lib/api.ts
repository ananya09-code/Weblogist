import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Scan } from "./types";
const API = import.meta.env.VITE_API_BASE_URL || "https://weblogist-production.up.railway.app";
async function json<T>(path: string, init?: RequestInit): Promise<T> { const r = await fetch(`${API}${path}`, init); const body = await r.json().catch(() => ({})); if (!r.ok) throw new Error(body.detail || `Request failed (${r.status})`); return body as T; }
export function useCreateScan() { const qc = useQueryClient(); return useMutation({ mutationFn: (url: string) => json<Scan>("/api/v1/scans", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) }), onSuccess: (scan) => qc.setQueryData(["scan", scan.scan_id], scan) }); }
export function useScan(id: string) { return useQuery({ queryKey: ["scan", id], queryFn: () => json<Scan>(`/api/v1/scans/${id}`), refetchInterval: (query) => { const s = query.state.data?.status; return s === "queued" || s === "running" ? 1500 : false; }, enabled: Boolean(id) }); }
