# 🛡️ SupplierShield

**Multi-Tier Supplier Risk & Resilience Analyzer**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0+-orange.svg)](https://networkx.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)

> A comprehensive supply chain risk management tool that maps multi-tier supplier networks, identifies vulnerabilities, simulates disruption scenarios using Monte Carlo analysis, and delivers actionable recommendations through an interactive Streamlit dashboard.

**Built by Andrei** | HBO University Venlo, Netherlands | International Business Program

---

## 🎯 The Problem

Modern electronics manufacturing depends on **multi-tiered global supply chains**. A manufacturer doesn't just buy from direct (Tier-1) suppliers—those Tier-1 suppliers depend on Tier-2 component makers, who depend on Tier-3 raw material providers. Most companies have **zero visibility** beyond Tier-1.

### Real-World Impact

When disruptions strike—COVID factory shutdowns, Suez Canal blockage (2021), Red Sea shipping crises (2024), semiconductor shortages, natural disasters—companies discover **too late** that a critical Tier-3 supplier in a high-risk region was feeding their entire production chain.

**The fictional case study (EuraTech BV, Venlo):**
- **2023:** Tier-2 semiconductor supplier in Malaysia shut down for 6 weeks due to flooding → **€2.1M in delayed production**
- **2024:** Tier-3 raw materials supplier in DR Congo faced export restrictions → 3 product lines delayed 4 weeks → **€800K in contract penalties**

In both cases, the procurement team had **no prior visibility** into these deep-tier dependencies.

---

## 💡 What SupplierShield Does

SupplierShield maps the full multi-tier supplier network (Tier-1 through Tier-3), overlays geopolitical, natural disaster, financial, and logistics risk data, and outputs:

### Core Capabilities

✅ **Network Graph Mapping** - Constructs directed acyclic graph (DAG) of 120 suppliers across 3 tiers with 237 dependency relationships

✅ **Multi-Dimensional Risk Scoring** - Composite 0-100 risk assessment across 5 weighted dimensions (geopolitical, natural disaster, financial, logistics, concentration)

✅ **Risk Propagation Analysis** - Bottom-up risk cascade revealing hidden vulnerabilities when safe suppliers depend on risky ones

✅ **SPOF Detection** - Identifies 17 critical single points of failure with downstream impact analysis (up to €55.4M value at risk)

✅ **Monte Carlo Disruption Simulation** - Probabilistic revenue-at-risk estimation with 1,000-10,000 iterations across single-node, regional, and correlated failure scenarios

✅ **Sensitivity Analysis** - Criticality ranking combining risk scores with revenue exposure; Pareto analysis showing 17.5% of suppliers drive 50% of total risk

✅ **BOM Impact Tracing** - Maps supplier failures to affected products and quantifies revenue-at-risk across the entire product portfolio

✅ **Actionable Recommendations** - Rule-based prioritized action plan with 59 recommendations across 4 severity levels and timelines

✅ **Interactive Dashboard** - 5-page Streamlit application with network visualization, heatmaps, Monte Carlo simulator, treemaps, and export capabilities

---

## 🔥 Key Insight: Hidden Vulnerability Example

**The Problem Traditional Analysis Misses:**

| Metric | Value | Interpretation |
|---|---|---|
| **Supplier** | S047 - Switzerland Global Industries | Based in very stable country |
| **Country Risk** | Switzerland (political: 5, disaster: 10, logistics: 95) | Excellent conditions |
| **Composite Risk** | 16.4/100 (LOW) | Looks completely safe |
| **Dependencies** | Depends on S009 (DR Congo, risk: 75.0 CRITICAL) | Hidden vulnerability! |
| **Propagated Risk** | 39.9/100 (MEDIUM) | True risk revealed |
| **Risk Increase** | **+23.4 points** | 143% increase from propagation |

**Business Impact:** A procurement manager looking only at composite risk would classify this as "low priority." Risk propagation reveals it's actually **medium risk** due to dangerous dependencies.

**The Math:**
```python
own_risk = 16.4
upstream_risk = 75.0  # S009 (DR Congo)

propagated = max(
    16.4,
    16.4 * 0.6 + 75.0 * 0.4
)
= max(16.4, 9.84 + 30.0)
= max(16.4, 39.84)
= 39.9
```

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.10 or higher
pip package manager
Git
```

### Installation
```bash
# Clone the repository
git clone https://github.com/andrei-motora/suppliershield.git
cd suppliershield

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Generate Synthetic Data
```bash
python scripts/generate_data.py
```

**Output:**
```
============================================================
SUPPLIERSHIELD DATA GENERATION
============================================================

[OK] Loaded 14 countries
Generating 40 Tier-3 suppliers...
Generating 40 Tier-2 suppliers...
Generating 40 Tier-1 suppliers...
[OK] Generated 120 total suppliers
[OK] Saved to data/raw/suppliers.csv

Generating supplier dependencies...
[OK] Generated 237 dependency edges
[OK] Saved to data/raw/dependencies.csv

Generating 10 product BOMs...
[OK] Generated 10 products
[OK] Saved to data/raw/product_bom.csv

============================================================
DATA GENERATION COMPLETE!
============================================================

Summary:
  - 120 suppliers across 3 tiers
  - 237 supplier dependencies
  - 10 products
  - 14 countries
```

### Run Complete Analysis Pipeline
```bash
# Network construction and validation
python scripts/test_network.py

# Risk scoring across 5 dimensions
python scripts/test_risk_scorer.py

# Risk propagation analysis
python scripts/test_risk_propagation.py

# SPOF detection and impact analysis
python scripts/test_spof_detector.py

# Monte Carlo disruption simulation
python scripts/test_monte_carlo.py

# Sensitivity analysis (criticality ranking)
python scripts/test_sensitivity.py

# Full Phase 3 integration test
python scripts/test_phase3_complete.py
```

### Launch Interactive Dashboard
```bash
streamlit run app/streamlit_app.py
```
Opens at `http://localhost:8501` with 5 interactive pages.

### Run Unit Tests
```bash
pytest tests/ -v
```
**29 tests, all passing.**

---

## 📊 Detailed Feature Breakdown

### Feature 1: Network Graph Construction

**What it does:** Converts supplier CSV data into a directed acyclic graph (DAG) using NetworkX.

**Network Structure:**
```
Tier-3 (Raw Materials: 40 suppliers)
   |
Tier-2 (Components: 40 suppliers)
   |
Tier-1 (Assemblies: 40 suppliers)
```

**Specifications:**
- **Nodes:** 120 suppliers with 12 attributes each (name, tier, country, contract value, financial health, etc.)
- **Edges:** 237 directed dependencies with weights (dependency percentage)
- **Graph Properties:**
  - Type: Directed Acyclic Graph (DAG) - no cycles
  - Density: 0.0166 (realistic sparsity)
  - Average degree: 1.98 connections per node
  - Validation: All tier transitions correct (T3 -> T2 -> T1 only)

**Validation Checks:**
```
[OK] Check 1: No cycles (DAG property) - PASS
[OK] Check 2: Network connectivity - PASS (4 components, 3 orphans)
[OK] Check 3: Correct tier flow - PASS (all edges follow T3 -> T2 -> T1)
[OK] Check 4: No self-loops - PASS
```

**Sample Node Attributes:**
```python
{
    'id': 'S081',
    'name': 'Japan International Systems',
    'tier': 1,
    'component': 'Assembled PCB Module',
    'country': 'Japan',
    'country_code': 'JP',
    'region': 'Asia-Pacific',
    'contract_value_eur_m': 1.56,
    'lead_time_days': 18,
    'financial_health': 90,
    'past_disruptions': 2,
    'has_backup': False
}
```

---

### Feature 2: Five-Dimension Risk Scoring

**Methodology:** Each supplier receives a composite risk score (0-100) based on five weighted dimensions.

#### Dimension Breakdown

| Dimension | Weight | Data Source | Calculation | Range |
|---|---|---|---|---|
| **Geopolitical Risk** | 30% | Country political stability index | Direct mapping | 0-100 (higher = more risk) |
| **Natural Disaster Risk** | 20% | Country disaster frequency index | Direct mapping | 0-100 (higher = more risk) |
| **Financial Risk** | 20% | Supplier financial health | 100 - financial_health | 0-100 (higher = more risk) |
| **Logistics Risk** | 15% | Country logistics performance | 100 - logistics_performance | 0-100 (higher = more risk) |
| **Concentration Risk** | 15% | Number of incoming suppliers | Algorithm-based | 0-100 (fewer alternatives = more risk) |

#### Composite Risk Formula
```python
composite_risk = (
    geopolitical_risk * 0.30 +
    natural_disaster_risk * 0.20 +
    financial_risk * 0.20 +
    logistics_risk * 0.15 +
    concentration_risk * 0.15
)

# Clamped to 0-100 range
composite_risk = min(100, max(0, composite_risk))
```

#### Concentration Risk Algorithm
```python
incoming_suppliers = count(edges where target == this_supplier)

if incoming_suppliers <= 1:
    if tier == 1:
        concentration_risk = 75  # Tier-1 with no backup is critical
    else:
        concentration_risk = 60  # Tier-2/3 with no backup
else:
    # Risk decreases with more suppliers
    concentration_risk = max(10, 60 - incoming_suppliers * 15)
```

#### Risk Categories

| Score Range | Category | Color | Action Level | Count |
|---|---|---|---|---|
| 0-34 | LOW | Green | Monitor normally | 44 suppliers |
| 35-54 | MEDIUM | Yellow | Review quarterly | 56 suppliers |
| 55-74 | HIGH | Orange | Action plan needed | 17 suppliers |
| 75-100 | CRITICAL | Red | Immediate action | 3 suppliers |

#### Validation Example: S024 (DR Congo)

**Input Data:**
```
Country: DR Congo
  - Political Stability: 85
  - Natural Disaster Freq: 60
  - Logistics Performance: 25
Supplier-Specific:
  - Financial Health: 2
  - Incoming Suppliers: 0
```

**Calculation:**
```
Geopolitical:    85.0 * 0.30 = 25.50
Natural Disaster: 60.0 * 0.20 = 12.00
Financial:       (100-2) * 0.20 = 19.60  # 98
Logistics:       (100-25) * 0.15 = 11.25  # 75
Concentration:   60.0 * 0.15 =  9.00  # No suppliers
                          ---------
Composite Risk:              77.35
Category: CRITICAL
```

#### Results Summary
```
Average risk score: 39.46/100
Min risk score: 5.75 (S089 - Switzerland)
Max risk score: 77.35 (S024 - DR Congo)
Median risk score: 39.80

Risk Distribution:
  - LOW (0-34): 44 suppliers (37%)
  - MEDIUM (35-54): 56 suppliers (47%)
  - HIGH (55-74): 17 suppliers (14%)
  - CRITICAL (75-100): 3 suppliers (2.5%)
```

---

### Feature 3: Risk Propagation Algorithm

**Purpose:** A Tier-1 supplier might look safe on its own, but if it depends on high-risk Tier-2 or Tier-3 suppliers, it's exposed. Risk propagation surfaces these hidden vulnerabilities.

#### Algorithm Steps

**Step 1: Initialize Tier-3**
```python
for supplier in tier_3:
    propagated_risk[supplier] = composite_risk[supplier]
# Tier-3 has no dependencies below it
```

**Step 2: Propagate to Tier-2**
```python
for supplier in tier_2:
    upstream = get_tier3_suppliers_feeding_into(supplier)

    if upstream:
        avg_upstream_risk = mean([propagated_risk[s] for s in upstream])

        propagated_risk[supplier] = max(
            composite_risk[supplier],
            composite_risk[supplier] * 0.6 + avg_upstream_risk * 0.4
        )
    else:
        propagated_risk[supplier] = composite_risk[supplier]
```

**Step 3: Propagate to Tier-1** (same formula as Step 2)

#### Key Design Decisions

- **`max()` function:** Ensures risk only increases, never decreases
- **60/40 split:** Supplier's own risk dominates (60%), but upstream risk can push it higher (40%)
- **Diamond dependencies:** Handled correctly (each node independently averages its children)

#### Propagation Results
```
Risk Propagation Summary:
  - Average risk increase: 2.74 points
  - Maximum risk increase: 23.40 points
  - Suppliers with increased risk: 47/120 (39%)

Propagated Risk Statistics:
  - Average: 42.20 (was 39.46)
  - Min: 13.41 (was 5.75)
  - Max: 77.35 (unchanged - already at top)
  - Median: 41.18 (was 39.80)
```

#### Top Risk Increases

| Rank | Supplier | Country | Composite | Propagated | Increase | Reason |
|---|---|---|---|---|---|---|
| 1 | S047 | Switzerland | 16.4 | 39.9 | **+23.4** | Depends on S009 (DR Congo, 75.0) |
| 2 | S050 | Germany | 25.2 | 46.1 | +20.9 | Depends on S024 (DR Congo, 77.3) |
| 3 | S089 | Switzerland | 5.8 | 23.1 | +17.4 | Depends on S049 (DR Congo, 73.2) |
| 4 | S041 | USA | 28.1 | 43.0 | +15.0 | Depends on S024 (DR Congo, 77.3) |

#### Hidden Vulnerabilities Detected

**Definition:** Suppliers with composite < 55 (MEDIUM or below) but propagated >= 55 (HIGH or above)
```
Found: 1 hidden vulnerability

S045 - China Superior Solutions
  Tier: 2
  Composite Risk: 45.2 [looks safe - MEDIUM]
  Propagated Risk: 57.0 [actually risky - HIGH]
  Hidden Vulnerability: +11.7 points
```

---

### Feature 4: SPOF Detection & Impact Analysis

**Definition:** A supplier is a Single Point of Failure (SPOF) if:
1. It has **no backup supplier** (has_backup = False)
2. AND one of:
   - High propagated risk (>60)
   - It's the only supplier for a downstream node
   - Its removal disconnects a critical path

#### Detection Results
```
SPOF Detection Summary:
  - Total SPOFs detected: 17

  SPOFs by Tier:
    - Tier-1: 6 SPOFs
    - Tier-2: 2 SPOFs
    - Tier-3: 9 SPOFs

  SPOFs by Reason:
    - High risk (>60): 10 SPOFs
    - Only supplier for downstream: 7 SPOFs
```

#### Most Impactful SPOFs

| Rank | Supplier | Tier | Contract | Direct Impact | Total Impact | Value at Risk | Risk |
|---|---|---|---|---|---|---|---|
| 1 | S016 - US Plastic | 3 | €0.77M | 4 suppliers | **20 suppliers** | **€55.4M** | 38.4 |
| 2 | S017 - India Plastic | 3 | €0.56M | 3 suppliers | 16 suppliers | €45.9M | 62.5 |
| 3 | S034 - Poland Silicon | 3 | €0.61M | 3 suppliers | 15 suppliers | €44.4M | 36.5 |
| 4 | S040 - Thailand Aluminum | 3 | €0.68M | 2 suppliers | 15 suppliers | €38.6M | 56.0 |

**Key Insight: S016 Impact Multiplier**
```
Contract Value: €0.77M
Value at Risk: €55.4M
Multiplier: 72x

Why? It feeds 4 Tier-2 suppliers, which feed 16 Tier-1 suppliers.
Cascading failure through the entire network.
```

#### Critical SPOFs (High Risk + No Backup)

**Found: 10 CRITICAL SPOFs** — all requiring immediate action (0-30 days):

| Supplier | Tier | Component | Country | Risk | Impact |
|---|---|---|---|---|---|
| S011 | 3 | Silicon Wafer | DR Congo | 74.5 | 8 suppliers, €23.3M |
| S017 | 3 | Plastic Resin | India | 62.5 | 16 suppliers, €45.9M |
| S049 | 2 | Semiconductor | DR Congo | 73.2 | 3 suppliers, €9.8M |
| S055 | 2 | Connector Set | DR Congo | 73.0 | 2 suppliers, €8.5M |
| S083 | 1 | Housing | DR Congo | 67.5 | 0 suppliers, €1.9M |
| S085 | 1 | PCB Module | DR Congo | 66.8 | 0 suppliers, €4.3M |
| S097 | 1 | PCB Module | DR Congo | 70.2 | 0 suppliers, €2.8M |
| S103 | 1 | Battery Pack | DR Congo | 69.8 | 0 suppliers, €2.5M |
| S108 | 1 | Display Panel | DR Congo | 70.2 | 0 suppliers, €5.0M |
| S120 | 1 | Display Panel | DR Congo | 71.0 | 0 suppliers, €4.6M |

**Pattern:** 9 out of 10 critical SPOFs are in **DR Congo** (most unstable country in the dataset)

---

### Feature 5: Monte Carlo Disruption Simulation

**Purpose:** Quantify revenue-at-risk from supplier disruptions through probabilistic simulation.

#### How It Works

1. **Select a target** — single supplier or entire region
2. **Set disruption duration** — 7 to 90 days
3. **Run 1,000-10,000 iterations** — each iteration randomly determines which suppliers fail based on their risk score and disruption duration
4. **Calculate revenue impact** — for each failed supplier, trace which products are affected via the BOM

#### Failure Probability Model
```python
base_probability = propagated_risk / 100.0
duration_factor = min(duration_days / 30.0, 1.5)  # Cap at 1.5x
failure_probability = min(base_probability * duration_factor, 0.95)
```

#### Scenario Types

| Scenario | Description | Example |
|---|---|---|
| **Single Node** | Target supplier + all downstream dependents | S024 (DR Congo) fails for 30 days |
| **Regional** | All suppliers in the same region | Asia-Pacific regional disruption |
| **Correlated** | Suppliers sharing upstream dependencies | Correlated supply chain failure |

#### Sample Results (S024 — DR Congo, 30 days, 5,000 iterations)
```
Simulation Results:
  - Mean impact: €8.71M
  - Median impact (P50): €8.77M
  - 95th percentile (P95): €14.13M
  - 99th percentile (P99): €15.86M
  - Worst case: €18.52M
  - Standard deviation: €3.36M
```

#### Scenario Comparison
```
                       Scenario        Type Mean Impact P95 Impact Worst Case
      S024 - DR Congo (30 days) Single Node      €8.71M    €14.13M    €18.52M
Asia-Pacific Regional (21 days)    Regional     €10.73M    €16.94M    €22.27M
       S016 - US SPOF (45 days) Single Node     €15.66M    €19.69M    €23.46M
```

---

### Feature 6: Sensitivity Analysis & Criticality Ranking

**Purpose:** Answer "Which single supplier failure would cause the most damage?" by combining risk with revenue exposure.

#### Criticality Formula
```python
criticality = (propagated_risk / 100) * total_revenue_exposure
```

Where `total_revenue_exposure = direct_revenue + (indirect_revenue * 0.5)`

#### Top 5 Most Critical Suppliers

| Rank | Supplier | Criticality | Risk | Exposure | Country |
|---|---|---|---|---|---|
| 1 | S017 - India Advanced Industries | 30.95 | 62.5 (HIGH) | €49.56M | India |
| 2 | S024 - DR Congo Superior Mfg | 30.33 | 77.3 (CRITICAL) | €39.21M | DR Congo |
| 3 | S016 - US Global Industries | 29.99 | 38.4 (MEDIUM) | €78.19M | US |
| 4 | S014 - Thailand Intl Industries | 23.13 | 53.8 (MEDIUM) | €43.02M | Thailand |
| 5 | S040 - Thailand Intl Mfg | 22.86 | 56.0 (HIGH) | €40.86M | Thailand |

#### Pareto Analysis (80/20 Rule)
```
Total Suppliers: 120
Total Criticality: 773.59

- 50% of criticality comes from: 21 suppliers (17.5%)
- 80% of criticality comes from: 51 suppliers (42.5%)
- Top 10 suppliers account for: 30.7% of total criticality
```

#### Risk vs Exposure Matrix

| Category | Count | Description |
|---|---|---|
| High Risk & High Exposure (CRITICAL) | 4 | Highest priority — both dangerous and impactful |
| High Risk & Low Exposure (Monitor) | 10 | Dangerous but limited blast radius |
| Low Risk & High Exposure (SPOF Candidate) | 26 | Safe now, but catastrophic if they fail |
| Low Risk & Low Exposure (OK) | 80 | Acceptable risk level |

---

### Feature 7: BOM Impact Tracing

**Purpose:** Map supplier failures to affected products and quantify revenue-at-risk.

#### How It Works

1. Identify the target supplier
2. Find all downstream suppliers via graph traversal
3. Cross-reference against product BOM (Bill of Materials)
4. Calculate revenue impact per product

#### Example: S017 Failure Impact
```
Supplier: S017 - India Advanced Industries (Tier-3, Plastic Resin)

Total affected suppliers: 17
  - Direct: 1 (S017)
  - Downstream cascade: 16

Affected Products: 8 out of 10
Total Revenue at Risk: €47.10M

Product Impact Breakdown:
  P004 - Precision Monitor DX:    €8.22M (50% suppliers affected) - HIGH
  P008 - ConnectNode Gateway:     €6.62M (60% suppliers affected) - HIGH
  P005 - AutomationHub 5000:      €5.36M (57% suppliers affected) - HIGH
  P007 - PowerCore System:        €7.33M (25% suppliers affected) - MEDIUM
  P002 - Industrial Controller:   €7.15M (33% suppliers affected) - MEDIUM
```

---

### Feature 8: Recommendation Engine

**Purpose:** Generate prioritized, actionable risk mitigation recommendations.

#### Rule Set

The engine evaluates every supplier against rules including:
- SPOF with high risk → establish dual-sourcing
- High-value contract with no backup → qualify backup supplier
- Low financial health → monitor stability
- Regional concentration → diversify sourcing

#### Output Summary
```
Total Recommendations: 59
  - CRITICAL: 0
  - HIGH: 19 (30-60 days)
  - MEDIUM: 17 (60-90 days)
  - WATCH: 23 (ongoing monitoring)

Contract Value at Risk:
  - HIGH priority suppliers: €50.44M
  - 40 unique suppliers require action
  - 9 countries affected
```

---

### Feature 9: Interactive Streamlit Dashboard

**5-page interactive application** with dark theme and orange accent styling.

#### Pages

| Page | Description | Key Visualizations |
|---|---|---|
| **Risk Overview** | Network-wide KPIs, risk gauges, category distribution | Gauge charts, donut chart, interactive network graph |
| **Risk Rankings** | Filterable supplier table with risk heatmap | Styled dataframe, 5-dimension heatmap, top-10 analysis |
| **What-If Simulator** | Monte Carlo disruption scenarios | Impact distribution histogram, percentile stats, management summary |
| **Sensitivity Analysis** | Criticality ranking and risk matrix | Treemap, bubble chart, country bar chart, tier comparison |
| **Recommendations** | Prioritized action items with severity levels | Severity-coded cards, donut summary, CSV export |

#### Dashboard Features
- **Interactive network graph** with zoom, pan, and node filtering by tier/risk
- **Real-time Monte Carlo simulation** configurable from the UI
- **Downloadable reports** — CSV export of rankings and recommendations
- **Responsive layout** — works on any screen size

```bash
# Launch the dashboard
streamlit run app/streamlit_app.py
```

---

## 🛠️ Technology Stack

### Core Analytics Engine

| Technology | Version | Purpose | Why Chosen |
|---|---|---|---|
| **Python** | 3.10+ | Core language | Type hints, modern features, data science ecosystem |
| **NetworkX** | 3.6+ | Graph analysis | Industry standard for network algorithms, rich API |
| **Pandas** | 2.3+ | Data manipulation | Fast CSV processing, DataFrame operations |
| **NumPy** | 2.4+ | Numerical computation | Efficient array operations, statistical functions |

### Visualization & Dashboard

| Technology | Version | Purpose |
|---|---|---|
| **Streamlit** | 1.40+ | Interactive multi-page web dashboard |
| **Plotly** | 6.5+ | Interactive charts (histograms, treemaps, network graphs, gauges) |
| **Pytest** | 9.0+ | Unit testing framework (29 tests) |

### Future Roadmap

- **FastAPI** - REST API backend
- **React** - Web frontend
- **React Native** - Mobile app

---

## 📁 Project Structure
```
suppliershield/
├── README.md                          # This file
├── CLAUDE.md                          # Claude Code onboarding guide
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
│
├── src/                               # Core analytics engine (~3,500 lines)
│   ├── data/                          # Data generation & validation
│   │   ├── generator.py               # Synthetic data generator (343 lines)
│   │   ├── loader.py                  # Data validation module (209 lines)
│   │   └── schemas.py                 # Schema definitions
│   ├── network/                       # Graph construction
│   │   ├── builder.py                 # NetworkX graph builder (211 lines)
│   │   └── validator.py               # Network integrity checks (208 lines)
│   ├── risk/                          # Risk analysis modules
│   │   ├── config.py                  # Risk weights & thresholds
│   │   ├── scorer.py                  # Multi-dimensional risk scoring (286 lines)
│   │   ├── propagation.py            # Risk cascade algorithm (255 lines)
│   │   └── spof_detector.py          # SPOF detection & impact (285 lines)
│   ├── simulation/                    # Monte Carlo & sensitivity
│   │   ├── monte_carlo.py            # Disruption simulator (353 lines)
│   │   └── sensitivity.py            # Criticality ranking (386 lines)
│   ├── impact/                        # Product impact analysis
│   │   └── bom_tracer.py             # BOM-to-supplier tracing (411 lines)
│   └── recommendations/              # Action plan generation
│       └── engine.py                  # Rule-based recommendations (402 lines)
│
├── app/                               # Streamlit dashboard (~2,000 lines)
│   ├── streamlit_app.py              # Main app + Risk Overview page (535 lines)
│   ├── shared_styles.py              # Theme, colors, CSS, UI helpers (327 lines)
│   └── pages/
│       ├── 1_📊_Risk_Rankings.py     # Filterable risk table + heatmap (338 lines)
│       ├── 2_🎲_What_If_Simulator.py # Monte Carlo UI (300 lines)
│       ├── 3_📈_Sensitivity_Analysis.py # Criticality ranking (477 lines)
│       └── 4_📋_Recommendations.py   # Action items + export (389 lines)
│
├── scripts/                           # CLI entry points & validation scripts
│   ├── generate_data.py              # Data generation CLI
│   ├── validate_data.py              # Data validation CLI
│   ├── test_network.py               # Network construction test
│   ├── test_risk_scorer.py           # Risk scoring test
│   ├── test_risk_propagation.py      # Risk propagation test
│   ├── test_spof_detector.py         # SPOF detection test
│   ├── test_monte_carlo.py           # Monte Carlo test
│   ├── test_sensitivity.py           # Sensitivity analysis test
│   └── test_phase3_complete.py       # Full integration test
│
├── tests/                             # Unit tests (29 tests, all passing)
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_risk_scorer.py           # Risk scoring tests (10 tests)
│   ├── test_propagation.py           # Propagation tests (9 tests)
│   ├── test_spof_detector.py         # SPOF detection tests (5 tests)
│   └── test_monte_carlo.py           # Monte Carlo tests (5 tests)
│
└── data/raw/                          # Generated CSV files
    ├── suppliers.csv                  # 120 suppliers
    ├── dependencies.csv               # 237 edges
    ├── country_risk.csv               # 14 countries
    └── product_bom.csv                # 10 products
```

**Total Code:** ~8,000 lines of Python across 40+ modules

---

## 🎓 Methodology & Validation

### Data Generation Methodology

**Realistic Synthetic Data:**

1. **Country Risk Indices** - Based on real-world data ranges from:
   - World Bank Worldwide Governance Indicators (political stability)
   - ND-GAIN Climate Index (disaster frequency)
   - World Bank Logistics Performance Index

2. **Supplier Financial Health** - Correlated with country stability:
```python
   base_health = 100 - country_political_stability
   financial_health = clip(normal(base_health, std=20), 0, 100)
```

3. **Past Disruptions** - Poisson distribution based on disaster frequency:
```python
   lambda = (country_disaster_freq / 100) * 3
   past_disruptions = poisson(lambda)
```

4. **Contract Values** - Tier-based realistic ranges:
   - Tier-1: €1.5-5.0M (final assemblies are most valuable)
   - Tier-2: €0.5-2.5M (components)
   - Tier-3: €0.2-1.2M (raw materials)

5. **Network Topology:**
   - Each Tier-2 depends on 1-3 Tier-3 suppliers (realistic concentration)
   - Each Tier-1 depends on 2-5 Tier-2 suppliers (typical assembly complexity)
   - Random seed = 42 (reproducible generation)

### Validation Summary

| Validation | Method | Status |
|---|---|---|
| Network is DAG (no cycles) | `nx.is_directed_acyclic_graph()` | PASS |
| Correct tier flow (T3 -> T2 -> T1) | Edge direction check | PASS |
| No self-loops | Loop detection | PASS |
| Risk weights sum to 1.0 | Assertion check | PASS |
| All risk scores 0-100 | Range validation | PASS |
| Propagated risk >= composite | Monotonicity check | PASS |
| SPOF detection correctness | Manual verification | PASS |
| Monte Carlo convergence | Statistical validation | PASS |
| 29 unit tests | Pytest | ALL PASSING |

---

## 📈 Project Status & Roadmap

### Current Phase: Phase 5 Complete

**Completed Phases:**

- **Phase 1 - Data Layer** - Synthetic data generator, validation, 120 suppliers, 237 dependencies, 14 countries
- **Phase 2 - Network & Risk Engine** - Graph construction, 5-dimension risk scoring, risk propagation, SPOF detection
- **Phase 3 - Disruption Simulation** - Monte Carlo simulator (3 scenario types), sensitivity analysis, criticality ranking
- **Phase 4 - BOM & Recommendations** - BOM impact tracer, rule-based recommendation engine with 59 prioritized actions
- **Phase 5 - Interactive Dashboard & Testing** - 5-page Streamlit app, 29 unit tests, integration tests

### Upcoming

- **Phase 6 - API & Web Frontend** - FastAPI REST backend, React web app
- **Phase 7 - Mobile & Production** - React Native app, containerization, CI/CD

---

## 🎯 Business Impact & Use Cases

### For Procurement Teams

**Problem:** "We had no idea a Malaysian supplier was at risk until it flooded."

**Solution:**
- Identify high-risk suppliers requiring immediate backup qualification
- Understand true supply chain exposure beyond Tier-1
- Prioritize risk mitigation investments by actual impact (not just contract value)

**Value Delivered:**
- 17 SPOFs identified with prioritized action plan
- 10 critical suppliers flagged for 0-30 day action
- €30.7M in SPOF contract value quantified

### For Risk Managers

**Problem:** "How much revenue is really at risk if China shuts down?"

**Solution:**
- Run Monte Carlo simulations to quantify revenue-at-risk probabilistically
- Detect hidden vulnerabilities in multi-tier dependencies
- Monitor concentration risk by region/country through the interactive dashboard

**Value Delivered:**
- Revenue impact quantified: €8.71M mean, €18.52M worst case (single supplier)
- Regional disruption modeled: Asia-Pacific event = €10.73M expected loss
- 1 hidden vulnerability revealed (S045: looked safe, actually high-risk)

### For Supply Chain Directors

**Problem:** "Where should we invest in supply chain resilience?"

**Solution:**
- Data-driven supplier diversification strategy via sensitivity analysis
- SPOF elimination roadmap with timelines and severity levels
- Interactive dashboard for exploring scenarios and exporting reports

**Value Delivered:**
- 72x impact multiplier discovered (S016: €0.77M contract -> €55.4M at risk)
- Pareto insight: just 21 suppliers (17.5%) drive 50% of total risk
- 59 actionable recommendations with priority levels and timelines

---

## 👨‍💻 Author

**Andrei**
International Business Student
HBO University of Applied Sciences, Venlo, Netherlands
Expected Graduation: 2029

*Building data-driven supply chain resilience tools for the Venlo-Limburg logistics corridor*

**Contact:**
[GitHub](https://github.com/andrei-motora) | LinkedIn

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
MIT License

Copyright (c) 2026 Andrei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🙏 Acknowledgments

- Portfolio project demonstrating supply chain analytics, graph theory, and Monte Carlo simulation
- Synthetic data methodology based on World Bank and ND-GAIN indices
- Designed for the Venlo-Limburg logistics and manufacturing industry
- Built with guidance on best practices for procurement risk management

---

## Important Notes

**This project uses synthetic data for demonstration purposes.**

For production use with real supplier data:
- Ensure proper data governance and privacy compliance
- Validate risk indices with actual supplier audits
- Integrate with ERP systems for real-time data
- Conduct sensitivity analysis on risk weights
- Validate network topology with procurement team
- Implement proper access controls and data encryption

**Academic Use:**
This project demonstrates proficiency in:
- Graph theory and network analysis
- Multi-dimensional risk modeling
- Monte Carlo simulation and probabilistic analysis
- Algorithm design and implementation
- Interactive data visualization (Streamlit + Plotly)
- Data validation and quality assurance
- Python software engineering best practices

---

**Last Updated:** February 2026
**Version:** 5.0 (Phase 5 Complete)
**Status:** Active Development
