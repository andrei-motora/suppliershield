# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SupplierShield is a supply chain risk analytics platform that maps multi-tier supplier networks, scores risk across 5 dimensions, propagates hidden vulnerabilities, detects single points of failure (SPOFs), and runs Monte Carlo disruption simulations. Built in phases: data generation → network graph → risk engine → simulation → Streamlit dashboard → (planned) FastAPI + React.

## Commands

```bash
# Install dependencies
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

# Launch Streamlit dashboard
streamlit run app/streamlit_app.py
```

## Architecture

**Pipeline flow**: Data (CSV) → NetworkX DiGraph → Risk Scoring → Risk Propagation → SPOF Detection → Simulation → Dashboard

```
src/
├── data/          # generator.py creates 120 suppliers across 3 tiers, loader.py validates & loads CSVs
├── network/       # builder.py constructs directed graph (suppliers=nodes, dependencies=edges)
├── risk/          # scorer.py (5-dim weighted scoring), propagation.py (bottom-up cascade Tier3→1), spof_detector.py
├── simulation/    # monte_carlo.py (5000-iteration disruption sim), sensitivity.py (criticality ranking)
├── impact/        # bom_tracer.py maps supplier failures to affected products & revenue-at-risk
└── recommendations/ # engine.py generates prioritized actions with severity levels and timelines

app/               # Streamlit multi-page dashboard (pages/ has 4 views: Risk Rankings, What-If, Sensitivity, Recommendations)
scripts/           # CLI entry points for data generation and per-module validation
tests/             # Pytest unit tests with fixtures in conftest.py
data/raw/          # Generated CSVs: suppliers.csv, dependencies.csv, country_risk.csv, product_bom.csv
```

## Key Design Details

- **Risk scoring formula**: Geopolitical (30%) + Natural Disaster (20%) + Financial (20%) + Logistics (15%) + Concentration (15%), scale 0-100. Weights configurable via `src/risk/config.py` or `.env`.
- **Risk propagation**: `max(own_risk, own_risk × 0.6 + upstream_avg × 0.4)` — bottom-up cascade reveals hidden vulnerabilities from deep-tier suppliers.
- **SPOF criteria**: No backup supplier AND (high risk OR sole supplier OR critical path). Downstream impact multiplier up to 72x.
- **Monte Carlo**: Supports single-node, regional, and correlated failure modes. Output includes mean/std/min/max revenue impact.
- **Sensitivity ranking**: `criticality = (risk/100) × revenue_exposure`.
- **Reproducibility**: Random seed 42 used throughout for deterministic data generation.
- **Dashboard theme**: Dark theme with orange accent (#f97316).

## Testing

Tests in `tests/` use pytest. The `conftest.py` adds `src/` to `sys.path`. Test files mirror source modules (e.g., `test_risk_scorer.py` tests `src/risk/scorer.py`). Validation scripts in `scripts/` serve as integration/demo tests with printed output.
