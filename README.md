# 🛡️ SupplierShield

**Multi-tier supply chain risk analyzer — maps hidden vulnerabilities before they become million-euro disruptions.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 29 passing](https://img.shields.io/badge/tests-29%20passing-brightgreen.svg)](tests/)

*What if the safest supplier in your network is actually your biggest risk?*

## Screenshot

![Dashboard](docs/images/dashboard_overview.png)
*Dashboard screenshot coming soon.*

## The Story

Most companies know their Tier-1 suppliers. Almost none have visibility into Tier-2 or Tier-3 — the component makers and raw material providers buried deep in the chain. When a flood shuts down a factory in Malaysia or export restrictions hit DR Congo, procurement teams discover too late that their entire production depended on a single supplier they'd never heard of.

SupplierShield was built to catch exactly that. It maps **120 suppliers across 3 tiers**, scores each one across **5 risk dimensions**, then does something most tools don't: it propagates risk upward through the network. A Swiss supplier scored **16.4** — low risk, stable country, excellent logistics. But it depended entirely on a Tier-3 supplier in DR Congo with a risk score of **75.0**. After propagation, its true risk jumped to **39.9**. A **143% increase** that traditional analysis completely misses.

That's one supplier. SupplierShield found **17 single points of failure**, ran **Monte Carlo simulations** to quantify the financial damage, and generated **59 prioritized recommendations** — all surfaced through an interactive dashboard where you can simulate disruptions in real time.

## What It Found

- **17 SPOFs** identified — one with a **72x impact multiplier** (€0.77M contract exposing €55.4M in downstream value)
- **47 suppliers** with hidden risk increases revealed through bottom-up propagation
- **€50.44M** in high-priority contract value requiring immediate action
- **5,000 Monte Carlo iterations** per scenario — mean impact €13.43M, worst case €22.98M
- **21 suppliers (17.5%)** drive **50%** of total portfolio risk

## How It Works

`CSV → NetworkX Graph → Risk Scoring → Propagation → SPOF Detection → Monte Carlo Simulation → Streamlit Dashboard`

```
src/
├── data/              # Generate & validate 120 suppliers, 237 dependencies, 14 countries
├── network/           # Build directed acyclic graph, validate tier flow
├── risk/              # 5-dimension scoring, bottom-up propagation, SPOF detection
├── simulation/        # Monte Carlo disruption sim, sensitivity & criticality ranking
├── impact/            # BOM tracer — map supplier failures to product revenue-at-risk
└── recommendations/   # Rule-based engine — 59 prioritized actions with timelines

app/                   # Streamlit dashboard — 5 pages, dark theme, interactive charts
scripts/               # CLI entry points for each pipeline stage
tests/                 # 29 pytest unit tests
data/raw/              # Generated CSVs (suppliers, dependencies, country_risk, product_bom)
```

## Quick Start

> Requires **Python 3.10+**. Use a virtual environment.

```bash
git clone https://github.com/andrei-motora/suppliershield.git
cd suppliershield
pip install -r requirements.txt
python scripts/generate_data.py
streamlit run app/streamlit_app.py
```

## Author

**Andrei** — International Business, HBO University of Applied Sciences, Venlo.

I build data-driven tools that turn supply chain complexity into actionable risk intelligence.

[GitHub](https://github.com/andrei-motora) · LinkedIn

## License

MIT
