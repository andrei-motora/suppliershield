"""Pydantic response / request models for SupplierShield API."""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


# ── Supplier ──────────────────────────────────────────────

class SupplierRisk(BaseModel):
    geopolitical: float
    natural_disaster: float
    financial: float
    logistics: float
    concentration: float
    composite: float
    propagated: float
    category: str


class SupplierResponse(BaseModel):
    supplier_id: str
    name: str
    tier: int
    component: str
    country: str
    country_code: str
    region: str
    contract_value_eur_m: float
    lead_time_days: int
    financial_health: float
    past_disruptions: int
    has_backup: bool
    is_spof: bool
    risk: SupplierRisk


class RiskPathItem(BaseModel):
    node_id: str
    name: str
    tier: int
    risk_composite: float
    risk_propagated: float


class SupplierDetailResponse(SupplierResponse):
    upstream: List[str]
    downstream: List[str]
    risk_path: List[RiskPathItem]


# ── Network ───────────────────────────────────────────────

class NetworkStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    density: float
    avg_degree: float
    tier_counts: Dict[str, int]


class GraphNode(BaseModel):
    id: str
    name: str
    tier: int
    risk: float
    category: str
    contract_value: float
    is_spof: bool
    x: float
    y: float
    country_code: str


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float


class NetworkGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class CountryAggregation(BaseModel):
    country_code: str
    country_name: str
    supplier_count: int
    avg_risk: float
    risk_category: str
    total_contract_value: float


class CountryAggregationResponse(BaseModel):
    countries: List[CountryAggregation]


# ── Risk ──────────────────────────────────────────────────

class RiskOverviewResponse(BaseModel):
    avg_risk: float
    categories: Dict[str, int]
    total_suppliers: int


class RiskIncreaseItem(BaseModel):
    supplier_id: str
    name: str
    tier: int
    composite: float
    propagated: float
    increase: float


class HiddenVulnerability(BaseModel):
    supplier_id: str
    name: str
    tier: int
    composite: float
    propagated: float
    increase: float


class RiskPropagationResponse(BaseModel):
    biggest_increases: List[RiskIncreaseItem]
    hidden_vulnerabilities: List[HiddenVulnerability]
    hidden_count: int


# ── SPOF ──────────────────────────────────────────────────

class SPOFResponse(BaseModel):
    supplier_id: str
    name: str
    tier: int
    component: str
    country: str
    contract_value_eur_m: float
    composite_risk: float
    propagated_risk: float
    direct_impact: int
    total_impact: int
    has_backup: bool


class SPOFImpactResponse(BaseModel):
    spof_id: str
    name: str
    direct_downstream: int
    total_affected: int
    tier_1_affected: int
    tier_2_affected: int
    tier_3_affected: int
    total_contract_value_at_risk: float


# ── Simulation ────────────────────────────────────────────

class SimulationRequest(BaseModel):
    target_supplier: str
    duration_days: int = Field(default=30, ge=7, le=90)
    iterations: int = Field(default=5000, ge=1000, le=10000)
    scenario_type: Literal["single_node", "regional", "correlated"] = Field(default="single_node")


class HistogramData(BaseModel):
    counts: List[int]
    bin_edges: List[float]
    bin_centers: List[float]


class SimulationResponse(BaseModel):
    target_supplier: str
    duration_days: int
    iterations: int
    scenario_type: str
    affected_suppliers_count: int
    affected_products: List[str]
    mean: float
    median: float
    std: float
    min: float
    max: float
    p25: float
    p75: float
    p90: float
    p95: float
    p99: float
    histogram: HistogramData
    runtime: float


# ── Sensitivity ───────────────────────────────────────────

class CriticalityItem(BaseModel):
    rank: int
    supplier_id: str
    name: str
    tier: int
    country: str
    component: str
    contract_value_eur_m: float
    propagated_risk: float
    risk_category: str
    direct_revenue_exposure: float
    indirect_revenue_exposure: float
    total_revenue_exposure: float
    criticality_score: float
    affected_products: int
    downstream_suppliers: int


class CriticalityResponse(BaseModel):
    items: List[CriticalityItem]
    total_count: int


class ParetoResponse(BaseModel):
    total_suppliers: int
    total_criticality: float
    pareto_80_suppliers: int
    pareto_80_percent: float
    pareto_50_suppliers: int
    pareto_50_percent: float
    top_10_criticality: float
    top_10_percent: float


# ── Recommendations ───────────────────────────────────────

class RecommendationItem(BaseModel):
    supplier_id: str
    supplier_name: str
    tier: int
    country: str
    component: str
    rule_name: str
    severity: str
    action: str
    reason: str
    timeline: str
    impact_score: float
    propagated_risk: float
    contract_value: float


class RecommendationSummary(BaseModel):
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    watch_count: int
    critical_contract_value: float
    high_contract_value: float
    unique_suppliers: int
    unique_countries: int


# ── Upload ───────────────────────────────────────────────

class FileUploadResponse(BaseModel):
    status: str  # "success" or "error"
    file_type: str
    row_count: int = 0
    columns: List[str] = []
    errors: List[str] = []


class UploadStatusResponse(BaseModel):
    has_suppliers: bool = False
    has_dependencies: bool = False
    has_country_risk: bool = False
    has_product_bom: bool = False
    ready_to_finalize: bool = False
    baseline_country_count: int = 0


class ValidationErrorItem(BaseModel):
    file: str
    check: str
    message: str


class UploadFinalizeResponse(BaseModel):
    status: str  # "success" or "error"
    errors: List[ValidationErrorItem] = []
    stats: Dict = {}


class DemoLoadResponse(BaseModel):
    status: str
    stats: Dict = {}
