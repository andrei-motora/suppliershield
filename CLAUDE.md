# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SupplierShield is a supply chain risk analytics platform that maps multi-tier supplier networks, scores risk across 5 dimensions, propagates hidden vulnerabilities, detects single points of failure (SPOFs), and runs Monte Carlo disruption simulations. The platform has a FastAPI + React web application backed by a Python analytics engine.

## Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Generate synthetic data (creates CSV files in data/raw/)
python scripts/generate_data.py

# Run unit tests
pytest tests/
pytest tests/test_risk_scorer.py          # single test file
pytest tests/test_risk_scorer.py -k test_name  # single test

# Run validation/demo scripts (sequential pipeline)
python scripts/test_network.py
python scripts/test_risk_scorer.py
python scripts/test_risk_propagation.py
python scripts/test_spof_detector.py
python scripts/test_monte_carlo.py
python scripts/test_sensitivity.py
python scripts/test_phase3_complete.py    # integration test

# Launch FastAPI backend
uvicorn backend.main:app --reload --port 8000

# Launch React frontend (requires backend running)
cd frontend && npm install && npm run dev

# Frontend build (TypeScript compilation + Vite bundle)
cd frontend && npm run build

# Docker: run full stack (backend + frontend)
docker compose up --build
```

## Architecture

**Pipeline flow**: Data (CSV) → NetworkX DiGraph → Risk Scoring → Risk Propagation → SPOF Detection → Simulation → Dashboard/API

```
src/                              # Core Python analytics engine
├── data/                         # generator.py (120 suppliers, 3 tiers), loader.py (CSV validation), schemas.py
├── network/                      # builder.py (DiGraph construction), validator.py (DAG/cycle/tier validation)
├── risk/                         # scorer.py (5-dim weighted), propagation.py (bottom-up cascade), spof_detector.py, config.py
├── simulation/                   # monte_carlo.py (5000-iteration sim), sensitivity.py (criticality ranking)
├── impact/                       # bom_tracer.py (supplier failures → affected products & revenue-at-risk)
└── recommendations/              # engine.py (prioritized actions with severity levels and timelines)

backend/                          # FastAPI REST API
├── main.py                       # App entry, CORS, session middleware, global exception handler
├── dependencies.py               # SupplierShieldEngine factory & per-session dependency injection
├── schemas.py                    # Pydantic request/response models (25+ schemas)
├── session/                      # SessionManager (per-session engine instances) + signed cookie middleware
└── routers/                      # 9 router modules:
    ├── suppliers.py              #   GET /api/suppliers (list, detail, tiers)
    ├── risk.py                   #   GET /api/risk (scores, propagation, rankings)
    ├── spofs.py                  #   GET /api/spofs (SPOF detection results)
    ├── simulation.py             #   POST /api/simulation (Monte Carlo runs)
    ├── sensitivity.py            #   GET /api/sensitivity (criticality, pareto)
    ├── recommendations.py        #   GET /api/recommendations (prioritized actions)
    ├── network.py                #   GET /api/network (graph stats, layout)
    ├── upload.py                 #   POST /api/upload (CSV file upload per session)
    └── demo.py                   #   POST /api/demo (load sample dataset)

frontend/                         # React + TypeScript SPA
├── src/
│   ├── api/client.ts             # API client & fetch utilities
│   ├── pages/                    # Dashboard, RiskRankings, WhatIfSimulator, SensitivityAnalysis, Recommendations
│   ├── components/               # Reusable components (Layout, Sidebar, KPICard, RiskBadge, FilterBar, etc.)
│   ├── types/index.ts            # TypeScript type definitions
│   └── utils/exportCsv.ts       # CSV export utility
├── vite.config.ts                # Vite build config (proxies /api → localhost:8000 in dev)
└── tailwind.config.js            # Custom theme (shield-bg, shield-surface, shield-accent)

scripts/                          # CLI entry points for data generation and per-module validation
tests/                            # Pytest unit tests with fixtures in conftest.py
data/raw/                         # Generated CSVs: suppliers.csv, dependencies.csv, country_risk.csv, product_bom.csv
```

## Key Design Details

- **Risk scoring formula**: Geopolitical (30%) + Natural Disaster (20%) + Financial (20%) + Logistics (15%) + Concentration (15%), scale 0-100. Weights configurable via `src/risk/config.py` or env vars.
- **Risk propagation**: `max(own_risk, own_risk × 0.6 + upstream_avg × 0.4)` — bottom-up cascade reveals hidden vulnerabilities from deep-tier suppliers.
- **Risk thresholds**: LOW (0-34), MEDIUM (35-54), HIGH (55-74), CRITICAL (75-100). Defined in `src/risk/config.py`.
- **SPOF criteria**: No backup supplier AND (high risk OR sole supplier OR critical path). Downstream impact multiplier up to 72x.
- **Monte Carlo**: Supports single-node, regional, and correlated failure modes. Output includes mean/std/min/max revenue impact.
- **Sensitivity ranking**: `criticality = (risk/100) × revenue_exposure`.
- **Reproducibility**: Random seed 42 used throughout for deterministic data generation.

### Backend Session Architecture

The backend uses **per-session engine instances**, not a global singleton. Key flow:

1. `SessionMiddleware` manages signed cookie-based sessions (configurable TTL, default 2h)
2. `SessionManager` (in `backend/session/`) creates/retrieves `SupplierShieldEngine` instances per session
3. Users either upload CSV files via `/api/upload` or load sample data via `/api/demo`
4. Each engine runs the full analytics pipeline (`initialize()`) and pre-computes expensive results (`_warm_caches()`)
5. `get_session_engine()` is the FastAPI dependency that resolves the current session's engine

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | random (non-persistent) | Signs session cookies |
| `MAX_SESSIONS` | 100 | Concurrent session limit |
| `SESSION_TTL` | 7200 | Session expiry in seconds |
| `UPLOAD_DIR` | system temp | File upload storage path |
| `CORS_ORIGINS` | `localhost:5173,localhost:3000` | Allowed CORS origins |
| `MAX_FILE_SIZE_MB` | 50 | Upload size limit |

### Frontend

- **TypeScript path alias**: `@/*` maps to `src/*`
- **Dev proxy**: Vite proxies `/api` requests to `http://localhost:8000`
- **Theme**: Dark theme with orange accent (#f97316). Custom TailwindCSS palette: `shield-bg`, `shield-surface`, `shield-accent`. Fonts: Inter (sans), JetBrains Mono (mono).
- **No lint/format scripts**: No ESLint or Prettier configured.

## Tech Stack

- **Core engine**: Python 3.11, NetworkX, Pandas, NumPy
- **API**: FastAPI 0.115, Uvicorn, Pydantic 2.9, itsdangerous (session signing), python-multipart (file uploads)
- **Frontend**: React 18, TypeScript 5.5, Vite 5, TailwindCSS 3.4, React Query (TanStack), Plotly.js, React Router 6, Lucide icons
- **Infrastructure**: Docker Compose, Nginx (reverse proxy + static serving, 1-year asset caching, gzip)

## Testing

Tests in `tests/` use pytest. The `conftest.py` adds the project root to `sys.path`. Test files mirror source modules (e.g., `test_risk_scorer.py` tests `src/risk/scorer.py`). Validation scripts in `scripts/` serve as integration/demo tests with printed output.
