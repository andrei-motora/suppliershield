"""Recommendation endpoints."""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import RecommendationItem, RecommendationSummary

router = APIRouter()


@router.get("", response_model=List[RecommendationItem])
def list_recommendations(
    severity: Optional[str] = Query(None),
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """Get all recommendations, optionally filtered by severity."""
    recs = engine.get_recommendations()

    if severity:
        recs = [r for r in recs if r["severity"] == severity.upper()]

    return [RecommendationItem(**r) for r in recs]


@router.get("/summary", response_model=RecommendationSummary)
def recommendation_summary(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """Get executive summary of recommendations."""
    summary = engine.get_rec_summary()
    return RecommendationSummary(**summary)
