# SupplierShield

**Multi-tier supply chain risk analyzer that maps hidden vulnerabilities before they become million-euro disruptions.**

![Python](https://img.shields.io/badge/Python-3776AB?style=plastic&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=plastic&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=plastic&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=plastic&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=plastic&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=plastic&logo=tailwindcss&logoColor=white)
![NetworkX](https://img.shields.io/badge/NetworkX-4C8CBF?style=plastic)
![pandas](https://img.shields.io/badge/pandas-150458?style=plastic&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=plastic&logo=numpy&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=plastic&logo=plotly&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=plastic&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=plastic&logo=nginx&logoColor=white)

> *What if the safest supplier in your network is actually your biggest risk?*

![Demo](https://github.com/user-attachments/assets/fa948e05-ff54-4a87-aa60-ffa19163d7c3)

## The Problem

Most companies know their Tier-1 suppliers but have zero visibility into Tier-2 and Tier-3 — the component makers and raw material extractors where supply chains actually break. SupplierShield maps **120 suppliers across 3 tiers and 14 countries**, scores each across **5 risk dimensions**, and **propagates risk upward** through the dependency graph to expose what flat scoring misses.

**143% hidden risk increase** — a "safe" Swiss supplier's true score after propagation revealed its fragile Tier-3 dependency
**17 SPOFs found** — single points of failure with no backup supplier, high risk, or critical-path positioning
**72x downstream impact multiplier** — one small contract exposing tens of millions in cascading value

## What It Found

| Metric | Value | Why It Matters |
|---|---|---|
| **Single Points of Failure** | **17** detected, one with a **72x impact multiplier** | A small contract exposing tens of millions in downstream value |
| **Hidden Risk Increases** | **47 suppliers** re-scored after propagation | Tier-2 suppliers saw the largest average increase (+5.59 points) |
| **High-Priority Contract Value** | **50.44M** requiring action within 30-60 days | 19 recommendations at HIGH severity across 40 suppliers |
| **Monte Carlo Worst Case** | **22.98M** revenue impact (5,000 iterations) | P95 gives procurement a concrete contingency budget number |
| **Pareto Concentration** | **21 suppliers (17.5%)** drive **50%** of total risk | Focus mitigation on the critical few, not the trivial many |

## How It Works

```mermaid
flowchart LR
    A[📄 CSV Data] --> B[🔗 NetworkX Graph]
    B --> C[📊 Risk Scoring]
    C --> D[⬆️ Propagation]
    D --> E[⚠️ SPOF Detection]
    E --> F[🎲 Monte Carlo]
    F --> G[📈 Dashboard]

    style A fill:#1e293b,stroke:#f97316,color:#f8fafc
    style B fill:#1e293b,stroke:#f97316,color:#f8fafc
    style C fill:#1e293b,stroke:#f97316,color:#f8fafc
    style D fill:#1e293b,stroke:#f97316,color:#f8fafc
    style E fill:#1e293b,stroke:#f97316,color:#f8fafc
    style F fill:#1e293b,stroke:#f97316,color:#f8fafc
    style G fill:#1e293b,stroke:#f97316,color:#f8fafc
```

The engine builds a directed acyclic graph from supplier and dependency data, then scores every node across five weighted dimensions: geopolitical stability, natural disaster exposure, financial health, logistics performance, and supplier concentration. The **propagation step** cascades risk bottom-up from Tier-3 through Tier-1, exposing hidden vulnerabilities that flat scoring misses entirely.

From there, single points of failure are detected, **5,000-iteration Monte Carlo simulations** quantify financial exposure under disruption scenarios, and **prioritized recommendations** are generated with severity levels and action timelines.

### Upload Your Own Data

SupplierShield isn't locked to sample data. The platform uses a **session-based architecture** — each user gets an isolated engine instance. Upload your own CSV files (suppliers, dependencies, country risk, product BOM) through the web interface, and the full analytics pipeline runs against *your* supply chain. No data crosses between sessions, and everything expires automatically. Alternatively, load the built-in demo dataset with one click to explore the platform immediately.

## Key Features

- **Multi-tier risk propagation** — reveals hidden vulnerabilities that flat scoring misses, cascading risk from Tier-3 through Tier-1
- **SPOF detection with impact multipliers** — identifies suppliers where a single failure cascades across the network (up to 72x downstream exposure)
- **Monte Carlo disruption simulation** — single-node, regional, and correlated failure modes with statistical output (mean, P95, worst-case)
- **Upload your own supply chain data** — session-isolated, per-user engine instances with automatic expiry
- **Interactive React dashboard** — real-time What-If simulator, risk rankings, sensitivity analysis, and CSV export
- **9 REST API endpoints** — suppliers, risk scores, SPOFs, simulation, sensitivity, recommendations, network stats, upload, and demo
- **Prioritized recommendations engine** — 59 actions ranked by severity with 30/60/90-day timelines

## Quick Start

> Requires **Python 3.10+** and **Node.js 18+**.

```bash
git clone https://github.com/andrei-motora/suppliershield.git
cd suppliershield
pip install -r requirements.txt
python scripts/generate_data.py

# Option 1: Docker (recommended)
docker compose up --build

# Option 2: Manual
uvicorn backend.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** (dev) or **http://localhost** (Docker) and click **Load Demo Data** to explore.

## Author

**Andrei** — International Business, HBO University of Applied Sciences, Venlo.

I build data-driven tools that turn supply chain complexity into actionable risk intelligence.

[GitHub](https://github.com/andrei-motora)

## License

MIT
