"""Supplier endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import SupplierResponse, SupplierDetailResponse, SupplierRisk

router = APIRouter()


def _build_supplier(engine: SupplierShieldEngine, node_id: str) -> SupplierResponse:
    nd = engine.graph.nodes[node_id]
    risk_scores = engine.risk_scores.get(node_id, {})
    return SupplierResponse(
        supplier_id=node_id,
        name=nd["name"],
        tier=nd["tier"],
        component=nd["component"],
        country=nd["country"],
        country_code=nd["country_code"],
        region=nd["region"],
        contract_value_eur_m=nd["contract_value_eur_m"],
        lead_time_days=nd["lead_time_days"],
        financial_health=nd["financial_health"],
        past_disruptions=nd["past_disruptions"],
        has_backup=nd["has_backup"],
        is_spof=nd.get("is_spof", False),
        risk=SupplierRisk(
            geopolitical=risk_scores.get("geopolitical", 0),
            natural_disaster=risk_scores.get("natural_disaster", 0),
            financial=risk_scores.get("financial", 0),
            logistics=risk_scores.get("logistics", 0),
            concentration=risk_scores.get("concentration", 0),
            composite=risk_scores.get("composite", 0),
            propagated=nd.get("risk_propagated", risk_scores.get("composite", 0)),
            category=risk_scores.get("category", "UNKNOWN"),
        ),
    )


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    tier: Optional[int] = Query(None, ge=1, le=3),
    risk_category: Optional[str] = None,
    component: Optional[str] = None,
    country: Optional[str] = None,
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """List all suppliers with optional filters."""
    results = []
    for node_id in engine.graph.nodes():
        nd = engine.graph.nodes[node_id]
        if tier is not None and nd["tier"] != tier:
            continue
        if risk_category and nd.get("risk_category", "") != risk_category.upper():
            continue
        if component and nd["component"] != component:
            continue
        if country and nd["country"] != country:
            continue
        results.append(_build_supplier(engine, node_id))
    return results


@router.get("/{supplier_id}", response_model=SupplierDetailResponse)
def get_supplier(
    supplier_id: str,
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """Get detailed info for a single supplier."""
    if supplier_id not in engine.graph.nodes():
        raise HTTPException(status_code=404, detail="Supplier not found")

    base = _build_supplier(engine, supplier_id)
    deps = engine.builder.get_supplier_dependencies(supplier_id)
    risk_path = engine.propagator.trace_risk_path(supplier_id)

    return SupplierDetailResponse(
        **base.model_dump(),
        upstream=deps["upstream"],
        downstream=deps["downstream"],
        risk_path=risk_path,
    )
