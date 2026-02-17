"""File upload endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query

from ..dependencies import get_session_id, create_engine_from_dir
from ..schemas import FileUploadResponse, UploadStatusResponse, UploadFinalizeResponse, ValidationErrorItem
from ..storage.file_handler import FileHandler, VALID_FILE_TYPES

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_file_handler(request: Request) -> FileHandler:
    """Get a FileHandler backed by the session manager's base dir."""
    return FileHandler(request.app.state.session_manager.base_dir)


@router.post("/file", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file_type: str = Query(..., description="One of: suppliers, dependencies, country_risk, product_bom"),
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id),
):
    """Upload and validate a single CSV file."""
    if file_type not in VALID_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file_type. Must be one of: {', '.join(sorted(VALID_FILE_TYPES))}",
        )

    handler = _get_file_handler(request)
    session_manager = request.app.state.session_manager
    session_dir = session_manager.get_session_dir(session_id)

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    result = handler.validate_and_save(session_dir, file_type, content)

    return FileUploadResponse(
        status="success" if result.valid else "error",
        file_type=result.file_type,
        row_count=result.row_count,
        columns=result.columns,
        errors=result.errors,
    )


@router.get("/status", response_model=UploadStatusResponse)
def upload_status(
    request: Request,
    session_id: str = Depends(get_session_id),
):
    """Check which files have been uploaded for this session."""
    handler = _get_file_handler(request)
    session_manager = request.app.state.session_manager
    session_dir = session_manager.get_session_dir(session_id)
    status = handler.get_upload_status(session_dir)
    return UploadStatusResponse(**status)


@router.post("/finalize", response_model=UploadFinalizeResponse)
def finalize_upload(
    request: Request,
    session_id: str = Depends(get_session_id),
):
    """Cross-validate all 4 files and build the analytics engine."""
    handler = _get_file_handler(request)
    session_manager = request.app.state.session_manager
    session_dir = session_manager.get_session_dir(session_id)

    # Check required files present (country_risk is optional)
    REQUIRED_FILES = {"suppliers", "dependencies", "product_bom"}
    status = handler.get_upload_status(session_dir)
    if not status["ready_to_finalize"]:
        missing = [ft for ft in REQUIRED_FILES if not status.get(f"has_{ft}", False)]
        raise HTTPException(
            status_code=400,
            detail=f"Missing required files: {', '.join(missing)}",
        )

    # Cross-validate
    validation_errors = handler.run_cross_validation(session_dir)
    if validation_errors:
        return UploadFinalizeResponse(
            status="error",
            errors=[
                ValidationErrorItem(file=e.file, check=e.check, message=e.message)
                for e in validation_errors
            ],
            stats={},
        )

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

        return UploadFinalizeResponse(status="success", errors=[], stats=stats)

    except Exception as e:
        logger.exception("Engine build failed for session %s", session_id[:8])
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build analytics engine: {e}",
        )
    finally:
        session_manager.release_build_semaphore()


@router.delete("/reset")
def reset_upload(
    request: Request,
    session_id: str = Depends(get_session_id),
):
    """Clear uploaded files and destroy the session engine."""
    session_manager = request.app.state.session_manager
    session_manager.destroy_session(session_id)
    # Create a fresh session with the same ID
    # (The middleware will assign a new session cookie on next request)
    return {"status": "ok", "message": "Session data cleared"}
