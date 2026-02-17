"""
SupplierShield — FastAPI Backend

Wraps the existing Python analytics engine with a REST API.
Per-session engine instances are managed via SessionManager.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .session.manager import SessionManager
from .session.middleware import SessionMiddleware
from .routers import suppliers, risk, spofs, simulation, sensitivity, recommendations, network
from .routers import upload, demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create SessionManager. Shutdown: clean up."""
    max_sessions = int(os.environ.get("MAX_SESSIONS", "100"))
    ttl = int(os.environ.get("SESSION_TTL", "7200"))
    upload_dir = os.environ.get("UPLOAD_DIR", None)

    app.state.session_manager = SessionManager(
        base_dir=upload_dir,
        max_sessions=max_sessions,
        ttl_seconds=ttl,
    )
    logger.info("SessionManager ready (max=%d, ttl=%ds)", max_sessions, ttl)
    yield
    app.state.session_manager.shutdown()


app = FastAPI(
    title="SupplierShield API",
    description="Supply-chain risk analytics REST API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — configurable via environment variable
_default_origins = "http://localhost:5173,http://localhost:3000"
cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware — signed cookie management
_secret_key = os.environ.get("SECRET_KEY", "")
if not _secret_key:
    import secrets
    _secret_key = secrets.token_urlsafe(32)
    logger.warning("No SECRET_KEY set — using random key. Sessions will not survive restarts.")
_session_ttl = int(os.environ.get("SESSION_TTL", "7200"))
app.add_middleware(SessionMiddleware, secret_key=_secret_key, max_age=_session_ttl)


# Global exception handler — prevent stack trace leaks
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Mount routers
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(risk.router,     prefix="/api/risk",      tags=["Risk"])
app.include_router(spofs.router,    prefix="/api/spofs",     tags=["SPOFs"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(sensitivity.router, prefix="/api/sensitivity", tags=["Sensitivity"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(network.router,  prefix="/api/network",   tags=["Network"])
app.include_router(upload.router,   prefix="/api/upload",    tags=["Upload"])
app.include_router(demo.router,     prefix="/api/demo",      tags=["Demo"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SupplierShield API"}
