# SupplierShield

**Multi-tier supply chain risk analyzer that maps hidden vulnerabilities before they become million-euro disruptions.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![NetworkX](https://img.shields.io/badge/NetworkX-4C8CBF?style=flat)
![pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat&logo=nginx&logoColor=white)

> *What if the safest supplier in your network is actually your biggest risk?*

![Demo](https://github.com/user-attachments/assets/fa948e05-ff54-4a87-aa60-ffa19163d7c3)

---

## The Problem

Most companies know their Tier-1 suppliers by name. They've negotiated contracts, visited factories, run audits. But ask them who supplies *those* suppliers — the component makers in Southeast Asia, the raw material extractors in Central Africa — and you get silence. This is the Tier-2 and Tier-3 blind spot, and it's where supply chains actually break.

When a flood shuts down a factory in Malaysia, when export restrictions hit the Democratic Republic of Congo, when a key logistics corridor gets disrupted, procurement teams discover — too late — that their entire production depended on a single supplier they'd never heard of. The contract was worth less than a million euros. The cascading damage reached tens of millions.

This isn't a hypothetical. SupplierShield was built to model exactly this scenario. It takes a network of **120 suppliers across 3 tiers and 14 countries**, scores each one across **5 risk dimensions**, and then does something most supply chain tools don't: it **propagates risk upward** through the dependency graph. A Swiss supplier scored **16.4** — low risk, stable country, excellent logistics. But it depended entirely on a Tier-3 supplier in DR Congo with a risk score of **75.0**. After propagation, its true risk jumped to **39.9** — a **143% increase** that traditional flat-scoring completely misses. That's one supplier. SupplierShield found **17 single points of failure** across the entire network.

---

## What It Found

| Metric | Value | Why It Matters |
|---|---|---|
| **Single Points of Failure** | **17** detected, one with a **72x impact multiplier** | A small contract exposing tens of millions in downstream value |
| **Hidden Risk Increases** | **47 suppliers** re-scored after propagation | Tier-2 suppliers saw the largest average increase (+5.59 points) |
| **High-Priority Contract Value** | **50.44M** requiring action within 30-60 days | 19 recommendations at HIGH severity across 40 suppliers |
| **Monte Carlo Worst Case** | **22.98M** revenue impact (5,000 iterations) | P95 gives procurement a concrete contingency budget number |
| **Pareto Concentration** | **21 suppliers (17.5%)** drive **50%** of total risk | Focus mitigation on the critical few, not the trivial many |

---

## How It Works

```
CSV Data  -->  NetworkX Graph  -->  Risk Scoring  -->  Propagation  -->  SPOF Detection  -->  Monte Carlo  -->  Dashboard
```

The analytics engine builds a directed acyclic graph from raw supplier and dependency data, then scores every node across five weighted dimensions: geopolitical stability, natural disaster exposure, financial health, logistics performance, and supplier concentration. What makes SupplierShield different is the **propagation step** — risk doesn't stay isolated at the node level. It cascades bottom-up from Tier-3 through Tier-2 to Tier-1, exposing hidden vulnerabilities that flat scoring misses entirely. A supplier can look safe on paper while sitting on top of a fragile dependency chain.

From there, the engine detects single points of failure (suppliers with no backup, high risk, or critical-path positioning), runs **5,000-iteration Monte Carlo simulations** to quantify financial exposure under disruption scenarios, and generates **prioritized recommendations** with severity levels and action timelines.

### Upload Your Own Data

SupplierShield isn't locked to sample data. The platform uses a **session-based architecture** — each user gets an isolated engine instance. Upload your own CSV files (suppliers, dependencies, country risk, product BOM) through the web interface, and the full analytics pipeline runs against *your* supply chain. No data crosses between sessions, and everything expires automatically. Alternatively, load the built-in demo dataset with one click to explore the platform immediately.

---

## Key Features

- **Multi-tier risk propagation** — reveals hidden vulnerabilities that flat scoring misses, cascading risk from Tier-3 through Tier-1
- **SPOF detection with impact multipliers** — identifies suppliers where a single failure cascades across the network (up to 72x downstream exposure)
- **Monte Carlo disruption simulation** — single-node, regional, and correlated failure modes with statistical output (mean, P95, worst-case)
- **Upload your own supply chain data** — session-isolated, per-user engine instances with automatic expiry
- **Interactive React dashboard** — real-time What-If simulator, risk rankings, sensitivity analysis, and CSV export
- **9 REST API endpoints** — suppliers, risk scores, SPOFs, simulation, sensitivity, recommendations, network stats, upload, and demo
- **Prioritized recommendations engine** — 59 actions ranked by severity with 30/60/90-day timelines

---

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

---

## Author

**Andrei** — International Business, HBO University of Applied Sciences, Venlo.

I build data-driven tools that turn supply chain complexity into actionable risk intelligence.

[GitHub](https://github.com/andrei-motora)

---

## License

MIT
