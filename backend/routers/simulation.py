"""Monte Carlo simulation endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_session_engine, SupplierShieldEngine
from ..schemas import SimulationRequest, SimulationResponse, HistogramData

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=SimulationResponse)
def run_simulation(
    req: SimulationRequest,
    engine: SupplierShieldEngine = Depends(get_session_engine),
):
    """Run a Monte Carlo disruption simulation."""
    if req.target_supplier not in engine.graph.nodes():
        raise HTTPException(status_code=404, detail="Target supplier not found")

    # scenario_type is validated by Pydantic Literal type
    try:
        stats = engine.simulator.run_simulation(
            target_supplier=req.target_supplier,
            duration_days=req.duration_days,
            iterations=req.iterations,
            scenario_type=req.scenario_type,
        )

        histogram = engine.simulator.get_histogram_data(stats["all_results"])

        return SimulationResponse(
            target_supplier=stats["target_supplier"],
            duration_days=stats["duration_days"],
            iterations=stats["iterations"],
            scenario_type=stats["scenario_type"],
            affected_suppliers_count=stats["affected_suppliers_count"],
            affected_products=stats["affected_products"],
            mean=round(stats["mean"], 2),
            median=round(stats["median"], 2),
            std=round(stats["std"], 2),
            min=round(stats["min"], 2),
            max=round(stats["max"], 2),
            p25=round(stats["p25"], 2),
            p75=round(stats["p75"], 2),
            p90=round(stats["p90"], 2),
            p95=round(stats["p95"], 2),
            p99=round(stats["p99"], 2),
            histogram=HistogramData(**histogram),
            runtime=round(stats["runtime"], 3),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Simulation failed for supplier %s", req.target_supplier)
        raise HTTPException(
            status_code=500,
            detail="Simulation failed unexpectedly. Please try again.",
        )
