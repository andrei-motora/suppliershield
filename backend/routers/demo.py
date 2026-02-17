"""Demo data loading endpoint."""

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from ..dependencies import get_session_id, create_engine_from_dir
from ..schemas import DemoLoadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEMO_DATA_DIR = PROJECT_ROOT / "data" / "raw"


@router.post("/load", response_model=DemoLoadResponse)
def load_demo_data(
    request: Request,
    session_id: str = Depends(get_session_id),
):
    """Copy demo data into the session and build the analytics engine."""
    session_manager = request.app.state.session_manager
    session_dir = session_manager.get_session_dir(session_id)

    if not DEMO_DATA_DIR.exists():
        raise HTTPException(
            status_code=500,
            detail="Demo data not found. Please run 'python scripts/generate_data.py' first.",
        )

    # Copy demo CSV files to session directory
    for csv_file in DEMO_DATA_DIR.glob("*.csv"):
        shutil.copy2(csv_file, session_dir / csv_file.name)

    # Build engine
    if not session_manager.acquire_build_semaphore():
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent builds. Please try again shortly.",
        )

    try:
        engine = create_engine_from_dir(str(session_dir))
        session_manager.set_engine(session_id, engine)

        stats = {
            "total_suppliers": engine.graph.number_of_nodes(),
            "total_edges": engine.graph.number_of_edges(),
            "spof_count": len(engine.spofs),
            "avg_risk": engine.get_risk_overview()["avg_risk"],
        }

        return DemoLoadResponse(status="success", stats=stats)

    except Exception as e:
        logger.exception("Demo engine build failed for session %s", session_id[:8])
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build analytics engine: {e}",
        )
    finally:
        session_manager.release_build_semaphore()
