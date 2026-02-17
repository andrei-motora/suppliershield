/**
 * API client — typed fetch wrappers for every SupplierShield endpoint.
 *
 * In development Vite proxies /api → http://localhost:8000 so we use
 * relative URLs everywhere.
 */

import type {
  Supplier,
  SupplierDetail,
  NetworkStats,
  NetworkGraph,
  RiskOverview,
  SimulationRequest,
  SimulationResult,
  CriticalityItem,
  ParetoResult,
  SPOFItem,
  Recommendation,
  RecommendationSummary,
  CountryAggregation,
  FileUploadResult,
  UploadStatus,
  UploadFinalizeResult,
  DemoLoadResult,
} from "../types";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text);
  }
  return res.json();
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "include",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text);
  }
  return res.json();
}

async function del<T>(url: string): Promise<T> {
  const res = await fetch(url, { method: "DELETE", credentials: "include" });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text);
  }
  return res.json();
}

// ── Suppliers ─────────────────────────────────────────────
export const fetchSuppliers = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return get<Supplier[]>(`/api/suppliers${qs}`);
};

export const fetchSupplier = (id: string) =>
  get<SupplierDetail>(`/api/suppliers/${id}`);

// ── Network ───────────────────────────────────────────────
export const fetchNetworkStats = () => get<NetworkStats>("/api/network/stats");
export const fetchNetworkGraph = () => get<NetworkGraph>("/api/network/graph");

export const fetchCountryAggregation = () =>
  get<{ countries: CountryAggregation[] }>("/api/network/countries");

// ── Risk ──────────────────────────────────────────────────
export const fetchRiskOverview = () => get<RiskOverview>("/api/risk/overview");

// ── SPOFs ─────────────────────────────────────────────────
export const fetchSPOFs = () => get<SPOFItem[]>("/api/spofs");

// ── Simulation ────────────────────────────────────────────
export const runSimulation = (req: SimulationRequest) =>
  post<SimulationResult>("/api/simulation/run", req);

// ── Sensitivity ───────────────────────────────────────────
export const fetchCriticality = (topN = 20) =>
  get<{ items: CriticalityItem[]; total_count: number }>(
    `/api/sensitivity/criticality?top_n=${topN}`
  );

export const fetchPareto = () => get<ParetoResult>("/api/sensitivity/pareto");

// ── Recommendations ───────────────────────────────────────
export const fetchRecommendations = (severity?: string) => {
  const qs = severity ? `?severity=${severity}` : "";
  return get<Recommendation[]>(`/api/recommendations${qs}`);
};

export const fetchRecommendationSummary = () =>
  get<RecommendationSummary>("/api/recommendations/summary");

// ── Upload ────────────────────────────────────────────────
export const uploadFile = async (fileType: string, file: File): Promise<FileUploadResult> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`/api/upload/file?file_type=${encodeURIComponent(fileType)}`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text);
  }
  return res.json();
};

export const getUploadStatus = () => get<UploadStatus>("/api/upload/status");

export const finalizeUpload = () => post<UploadFinalizeResult>("/api/upload/finalize", {});

export const resetUpload = () => del<{ status: string; message: string }>("/api/upload/reset");

export const loadDemoData = () => post<DemoLoadResult>("/api/demo/load", {});
