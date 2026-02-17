"""SPOF (Single Point of Failure) endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import SPOFResponse, SPOFImpactResponse

router = APIRouter()


@router.get("", response_model=List[SPOFResponse])
def list_spofs(engine: SupplierShieldEngine = Depends(get_session_engine)):
    """List all Single Points of Failure."""
    details = engine.spof_detector.get_spof_details()
    return [SPOFResponse(**d) for d in details]


@router.get("/{supplier_id}/impact", response_model=SPOFImpactResponse)
def spof_impact(
    supplier_id: str,
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """Analyse the downstream impact if a specific SPOF fails."""
    if supplier_id not in engine.spofs:
        raise HTTPException(status_code=404, detail="Supplier is not a SPOF")

    result = engine.spof_detector.analyze_spof_impact(supplier_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return SPOFImpactResponse(**result)
