"""Risk overview and propagation endpoints."""

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import (
    RiskOverviewResponse,
    RiskPropagationResponse,
    RiskIncreaseItem,
    HiddenVulnerability,
)

router = APIRouter()


@router.get("/overview", response_model=RiskOverviewResponse)
def risk_overview(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """Get network-wide risk summary."""
    cached = engine.get_risk_overview()
    return RiskOverviewResponse(**cached)


@router.get("/propagation", response_model=RiskPropagationResponse)
def risk_propagation(
    top_n: int = Query(10, ge=1, le=50),
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """Get risk propagation analysis."""
    increases_raw = engine.propagator.get_biggest_risk_increases(top_n)
    biggest = [
        RiskIncreaseItem(
            supplier_id=sid,
            name=engine.graph.nodes[sid]["name"],
            tier=engine.graph.nodes[sid]["tier"],
            composite=comp,
            propagated=prop,
            increase=inc,
        )
        for sid, comp, prop, inc in increases_raw
    ]

    hidden_raw = engine.propagator.analyze_hidden_vulnerabilities()
    hidden = [
        HiddenVulnerability(**item)
        for item in hidden_raw["suppliers"]
    ]

    return RiskPropagationResponse(
        biggest_increases=biggest,
        hidden_vulnerabilities=hidden,
        hidden_count=hidden_raw["count"],
    )
