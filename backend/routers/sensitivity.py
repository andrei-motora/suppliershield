"""Sensitivity / criticality analysis endpoints."""

from fastapi import APIRouter, Depends, Query
from typing import List

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import CriticalityItem, CriticalityResponse, ParetoResponse

router = APIRouter()


@router.get("/criticality", response_model=CriticalityResponse)
def criticality_ranking(
    top_n: int = Query(20, ge=1, le=120),
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """Get supplier criticality ranking."""
    df = engine.get_criticality(top_n)
    items = [
        CriticalityItem(
            rank=idx,
            supplier_id=row["supplier_id"],
            name=row["name"],
            tier=row["tier"],
            country=row["country"],
            component=row["component"],
            contract_value_eur_m=row["contract_value_eur_m"],
            propagated_risk=round(row["propagated_risk"], 2),
            risk_category=row["risk_category"],
            direct_revenue_exposure=round(row["direct_revenue_exposure"], 2),
            indirect_revenue_exposure=round(row["indirect_revenue_exposure"], 2),
            total_revenue_exposure=round(row["total_revenue_exposure"], 2),
            criticality_score=round(row["criticality_score"], 2),
            affected_products=int(row["affected_products"]),
            downstream_suppliers=int(row["downstream_suppliers"]),
        )
        for idx, row in df.iterrows()
    ]
    return CriticalityResponse(items=items, total_count=len(items))


@router.get("/pareto", response_model=ParetoResponse)
def pareto_analysis(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """Get Pareto analysis of supplier criticality."""
    result = engine.get_pareto()
    return ParetoResponse(
        total_suppliers=result["total_suppliers"],
        total_criticality=round(result["total_criticality"], 2),
        pareto_80_suppliers=result["pareto_80_suppliers"],
        pareto_80_percent=round(result["pareto_80_percent"], 2),
        pareto_50_suppliers=result["pareto_50_suppliers"],
        pareto_50_percent=round(result["pareto_50_percent"], 2),
        top_10_criticality=round(result["top_10_criticality"], 2),
        top_10_percent=round(result["top_10_percent"], 2),
    )
