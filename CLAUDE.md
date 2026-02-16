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

# Docker: run full stack (backend + frontend)
docker compose up --build
```

## Architecture

**Pipeline flow**: Data (CSV) → NetworkX DiGraph → Risk Scoring → Risk Propagation → SPOF Detection → Simulation → Dashboard/API

```
src/                              # Core Python analytics engine
├── data/                         # generator.py (120 suppliers, 3 tiers), loader.py (CSV validation), schemas.py (data schemas)
├── network/                      # builder.py (DiGraph construction), validator.py (DAG/cycle/tier validation)
├── risk/                         # scorer.py (5-dim weighted), propagation.py (bottom-up cascade), spof_detector.py, config.py
├── simulation/                   # monte_carlo.py (5000-iteration sim), sensitivity.py (criticality ranking)
├── impact/                       # bom_tracer.py (supplier failures → affected products & revenue-at-risk)
└── recommendations/              # engine.py (prioritized actions with severity levels and timelines)

backend/                          # FastAPI REST API (Phase 2)
├── main.py                       # App entry point, CORS, startup caching
├── dependencies.py               # SupplierShieldEngine singleton & dependency injection
├── schemas.py                    # Pydantic request/response models (25+ schemas)
└── routers/                      # 7 router modules:
    ├── suppliers.py              #   GET /api/suppliers (list, detail, tiers)
    ├── risk.py                   #   GET /api/risk (scores, propagation, rankings)
    ├── spofs.py                  #   GET /api/spofs (SPOF detection results)
    ├── simulation.py             #   POST /api/simulation (Monte Carlo runs)
    ├── sensitivity.py            #   GET /api/sensitivity (criticality, pareto)
    ├── recommendations.py        #   GET /api/recommendations (prioritized actions)
    └── network.py                #   GET /api/network (graph stats, layout)

frontend/                         # React + TypeScript SPA (Phase 2)
├── src/
│   ├── api/client.ts             # API client & fetch utilities
│   ├── pages/                    # 5 pages: Dashboard, RiskRankings, WhatIfSimulator, SensitivityAnalysis, Recommendations
│   ├── components/               # 14 reusable components (Layout, Sidebar, KPICard, RiskBadge, FilterBar, etc.)
│   ├── types/index.ts            # TypeScript type definitions
│   └── utils/exportCsv.ts       # CSV export utility
├── Dockerfile                    # Multi-stage build (Node → Nginx)
├── nginx.conf                    # Reverse proxy config (API proxying, gzip, caching)
├── vite.config.ts                # Vite build config
└── tailwind.config.js            # Custom theme (shield-bg, shield-surface, shield-accent)

scripts/                          # CLI entry points for data generation and per-module validation
tests/                            # Pytest unit tests with fixtures in conftest.py
data/raw/                         # Generated CSVs: suppliers.csv, dependencies.csv, country_risk.csv, product_bom.csv
docker-compose.yml                # Orchestrates backend (:8000) + frontend (:3000) with health checks
```

## Key Design Details

- **Risk scoring formula**: Geopolitical (30%) + Natural Disaster (20%) + Financial (20%) + Logistics (15%) + Concentration (15%), scale 0-100. Weights configurable via `src/risk/config.py` or `.env`.
- **Risk propagation**: `max(own_risk, own_risk × 0.6 + upstream_avg × 0.4)` — bottom-up cascade reveals hidden vulnerabilities from deep-tier suppliers.
- **SPOF criteria**: No backup supplier AND (high risk OR sole supplier OR critical path). Downstream impact multiplier up to 72x.
- **Monte Carlo**: Supports single-node, regional, and correlated failure modes. Output includes mean/std/min/max revenue impact.
- **Sensitivity ranking**: `criticality = (risk/100) × revenue_exposure`.
- **Reproducibility**: Random seed 42 used throughout for deterministic data generation.
- **Theme**: Dark theme with orange accent (#f97316). Frontend uses TailwindCSS custom palette (shield-bg, shield-surface, shield-accent). Fonts: Inter (sans), JetBrains Mono (mono).
- **Backend singleton**: `SupplierShieldEngine` in `backend/dependencies.py` initializes the full analytics pipeline once at startup and pre-computes expensive operations (recommendations, criticality, pareto, graph layout).
- **API health check**: `GET /api/health` — used by Docker Compose for service readiness.

## Tech Stack

- **Core engine**: Python 3.11, NetworkX, Pandas, NumPy
- **API**: FastAPI 0.115, Uvicorn, Pydantic 2.9
- **Frontend**: React 18, TypeScript 5.5, Vite 5, TailwindCSS 3.4, React Query (TanStack), Plotly.js, React Router 6, Lucide icons
- **Infrastructure**: Docker Compose, Nginx (reverse proxy + static serving)

## Testing

Tests in `tests/` use pytest. The `conftest.py` adds `src/` to `sys.path`. Test files mirror source modules (e.g., `test_risk_scorer.py` tests `src/risk/scorer.py`). Validation scripts in `scripts/` serve as integration/demo tests with printed output.
