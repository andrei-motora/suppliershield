/* ── Shared TypeScript types (mirrors backend schemas.py) ── */

export interface SupplierRisk {
  geopolitical: number;
  natural_disaster: number;
  financial: number;
  logistics: number;
  concentration: number;
  composite: number;
  propagated: number;
  category: RiskCategory;
}

export type RiskCategory = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "WATCH";

export interface Supplier {
  supplier_id: string;
  name: string;
  tier: number;
  component: string;
  country: string;
  country_code: string;
  region: string;
  contract_value_eur_m: number;
  lead_time_days: number;
  financial_health: number;
  past_disruptions: number;
  has_backup: boolean;
  is_spof: boolean;
  risk: SupplierRisk;
}

export interface RiskPathItem {
  node_id: string;
  name: string;
  tier: number;
  risk_composite: number;
  risk_propagated: number;
}

export interface SupplierDetail extends Supplier {
  upstream: string[];
  downstream: string[];
  risk_path: RiskPathItem[];
}

export interface NetworkStats {
  total_nodes: number;
  total_edges: number;
  density: number;
  avg_degree: number;
  tier_counts: Record<string, number>;
}

export interface GraphNode {
  id: string;
  name: string;
  tier: number;
  risk: number;
  category: RiskCategory;
  contract_value: number;
  is_spof: boolean;
  x: number;
  y: number;
  country_code: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export interface NetworkGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RiskOverview {
  avg_risk: number;
  categories: Record<RiskCategory, number>;
  total_suppliers: number;
}

export interface HistogramData {
  counts: number[];
  bin_edges: number[];
  bin_centers: number[];
}

export interface SimulationRequest {
  target_supplier: string;
  duration_days: number;
  iterations: number;
  scenario_type: "single_node" | "regional" | "correlated";
}

export interface SimulationResult {
  target_supplier: string;
  duration_days: number;
  iterations: number;
  scenario_type: string;
  affected_suppliers_count: number;
  affected_products: string[];
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  p25: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
  histogram: HistogramData;
  runtime: number;
}

export interface CriticalityItem {
  rank: number;
  supplier_id: string;
  name: string;
  tier: number;
  country: string;
  component: string;
  contract_value_eur_m: number;
  propagated_risk: number;
  risk_category: RiskCategory;
  direct_revenue_exposure: number;
  indirect_revenue_exposure: number;
  total_revenue_exposure: number;
  criticality_score: number;
  affected_products: number;
  downstream_suppliers: number;
}

export interface ParetoResult {
  total_suppliers: number;
  total_criticality: number;
  pareto_80_suppliers: number;
  pareto_80_percent: number;
  pareto_50_suppliers: number;
  pareto_50_percent: number;
  top_10_criticality: number;
  top_10_percent: number;
}

export interface SPOFItem {
  supplier_id: string;
  name: string;
  tier: number;
  component: string;
  country: string;
  contract_value_eur_m: number;
  composite_risk: number;
  propagated_risk: number;
  direct_impact: number;
  total_impact: number;
  has_backup: boolean;
}

export interface Recommendation {
  supplier_id: string;
  supplier_name: string;
  tier: number;
  country: string;
  component: string;
  rule_name: string;
  severity: Severity;
  action: string;
  reason: string;
  timeline: string;
  impact_score: number;
  propagated_risk: number;
  contract_value: number;
}

export interface RecommendationSummary {
  total_recommendations: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  watch_count: number;
  critical_contract_value: number;
  high_contract_value: number;
  unique_suppliers: number;
  unique_countries: number;
}

// ── Country Aggregation ─────────────────────────────────

export interface CountryAggregation {
  country_code: string;
  country_name: string;
  supplier_count: number;
  avg_risk: number;
  risk_category: RiskCategory;
  total_contract_value: number;
}

// ── Upload ──────────────────────────────────────────────

export interface FileUploadResult {
  status: "success" | "error";
  file_type: string;
  row_count: number;
  columns: string[];
  errors: string[];
}

export interface UploadStatus {
  has_suppliers: boolean;
  has_dependencies: boolean;
  has_country_risk: boolean;
  has_product_bom: boolean;
  ready_to_finalize: boolean;
}

export interface ValidationError {
  file: string;
  check: string;
  message: string;
}

export interface UploadFinalizeResult {
  status: "success" | "error";
  errors: ValidationError[];
  stats: Record<string, number>;
}

export interface DemoLoadResult {
  status: string;
  stats: Record<string, number>;
}
