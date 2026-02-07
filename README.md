# 🛡️ SupplierShield

**Multi-Tier Supplier Risk & Resilience Analyzer**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0+-orange.svg)](https://networkx.org/)

> A comprehensive supply chain risk management tool that maps multi-tier supplier networks, identifies vulnerabilities, and simulates disruption scenarios using graph theory, Monte Carlo analysis, and advanced network analytics.

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

🔄 **Monte Carlo Disruption Simulation** - Probabilistic revenue-at-risk estimation *(coming in Phase 3)*

🔄 **Sensitivity Analysis** - Criticality ranking: which single supplier failure causes the most damage *(coming in Phase 3)*

🔄 **Actionable Recommendations** - Rule-based prioritized action plan with timelines *(coming in Phase 3)*

---

## 🔥 Key Insight: Hidden Vulnerability Example

**The Problem Traditional Analysis Misses:**

| Metric | Value | Interpretation |
|---|---|---|
| **Supplier** | S047 - Switzerland Global Industries | Based in very stable country |
| **Country Risk** | Switzerland (political: 5, disaster: 10, logistics: 95) | Excellent conditions |
| **Composite Risk** | 16.4/100 (LOW) | Looks completely safe ✓ |
| **Dependencies** | Depends on S009 (DR Congo, risk: 75.0 CRITICAL) | Hidden vulnerability! |
| **Propagated Risk** | 39.9/100 (MEDIUM) | True risk revealed ⚠️ |
| **Risk Increase** | **+23.4 points** | 143% increase from propagation |

**Business Impact:** A procurement manager looking only at composite risk would classify this as "low priority." Risk propagation reveals it's actually **medium risk** due to dangerous dependencies.

**The Math:**
```python
own_risk = 16.4
upstream_risk = 75.0  # S009 (DR Congo)

propagated = max(
    16.4,
    16.4 × 0.6 + 75.0 × 0.4
)
= max(16.4, 9.84 + 30.0)
= max(16.4, 39.84)
= 39.9 ✓
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

✓ Loaded 14 countries
Generating 40 Tier-3 suppliers...
Generating 40 Tier-2 suppliers...
Generating 40 Tier-1 suppliers...
✓ Generated 120 total suppliers
✓ Saved to data/raw/suppliers.csv

Generating supplier dependencies...
✓ Generated 237 dependency edges
✓ Saved to data/raw/dependencies.csv

Generating 10 product BOMs...
✓ Generated 10 products
✓ Saved to data/raw/product_bom.csv

============================================================
DATA GENERATION COMPLETE!
============================================================

Summary:
  • 120 suppliers across 3 tiers
  • 237 supplier dependencies
  • 10 products
  • 14 countries
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
```

---

## 📊 Detailed Feature Breakdown

### Feature 1: Network Graph Construction

**What it does:** Converts supplier CSV data into a directed acyclic graph (DAG) using NetworkX.

**Network Structure:**
```
Tier-3 (Raw Materials: 40 suppliers)
   ↓ 
Tier-2 (Components: 40 suppliers)
   ↓
Tier-1 (Assemblies: 40 suppliers)
```

**Specifications:**
- **Nodes:** 120 suppliers with 12 attributes each (name, tier, country, contract value, financial health, etc.)
- **Edges:** 237 directed dependencies with weights (dependency percentage)
- **Graph Properties:**
  - Type: Directed Acyclic Graph (DAG) - no cycles
  - Density: 0.0166 (realistic sparsity)
  - Average degree: 1.98 connections per node
  - Validation: All tier transitions correct (T3→T2→T1 only)

**Validation Checks:**
```
✓ Check 1: No cycles (DAG property) - PASS
✓ Check 2: Network connectivity - PASS (4 components, 3 orphans)
✓ Check 3: Correct tier flow - PASS (all edges follow T3→T2→T1)
✓ Check 4: No self-loops - PASS
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
    geopolitical_risk × 0.30 +
    natural_disaster_risk × 0.20 +
    financial_risk × 0.20 +
    logistics_risk × 0.15 +
    concentration_risk × 0.15
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
    concentration_risk = max(10, 60 - incoming_suppliers × 15)
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
  • Political Stability: 85
  • Natural Disaster Freq: 60
  • Logistics Performance: 25
Supplier-Specific:
  • Financial Health: 2
  • Incoming Suppliers: 0
```

**Calculation:**
```
Geopolitical:    85.0 × 0.30 = 25.50
Natural Disaster: 60.0 × 0.20 = 12.00
Financial:       (100-2) × 0.20 = 19.60  # 98
Logistics:       (100-25) × 0.15 = 11.25  # 75
Concentration:   60.0 × 0.15 =  9.00  # No suppliers
                          ─────────
Composite Risk:              77.35 ✓
Category: CRITICAL
```

**Comparison: S089 (Switzerland)**
```
Geopolitical:     5.0 × 0.30 =  1.50
Natural Disaster: 10.0 × 0.20 =  2.00
Financial:        5.0 × 0.20 =  1.00  # health: 95
Logistics:        5.0 × 0.15 =  0.75  # perf: 95
Concentration:   10.0 × 0.15 =  1.50  # 4 suppliers
                          ────────
Composite Risk:               5.75 ✓
Category: LOW
```

#### Results Summary
```
Average risk score: 39.46/100
Min risk score: 5.75 (S089 - Switzerland)
Max risk score: 77.35 (S024 - DR Congo)
Median risk score: 39.80

Risk Distribution:
  • LOW (0-34): 44 suppliers (37%)
  • MEDIUM (35-54): 56 suppliers (47%)
  • HIGH (55-74): 17 suppliers (14%)
  • CRITICAL (75-100): 3 suppliers (2.5%)
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
            composite_risk[supplier] × 0.6 + avg_upstream_risk × 0.4
        )
    else:
        propagated_risk[supplier] = composite_risk[supplier]
```

**Step 3: Propagate to Tier-1**
```python
for supplier in tier_1:
    upstream = get_tier2_suppliers_feeding_into(supplier)
    
    if upstream:
        avg_upstream_risk = mean([propagated_risk[s] for s in upstream])
        
        propagated_risk[supplier] = max(
            composite_risk[supplier],
            composite_risk[supplier] × 0.6 + avg_upstream_risk × 0.4
        )
    else:
        propagated_risk[supplier] = composite_risk[supplier]
```

#### Key Design Decisions

- **`max()` function:** Ensures risk only increases, never decreases
- **60/40 split:** Supplier's own risk dominates (60%), but upstream risk can push it higher (40%)
- **Diamond dependencies:** Handled correctly (each node independently averages its children)

#### Propagation Results
```
Risk Propagation Summary:
  • Average risk increase: 2.74 points
  • Maximum risk increase: 23.40 points
  • Suppliers with increased risk: 47/120 (39%)

Propagated Risk Statistics:
  • Average: 42.20 (was 39.46)
  • Min: 13.41 (was 5.75)
  • Max: 77.35 (unchanged - already at top)
  • Median: 41.18 (was 39.80)
```

#### Top Risk Increases

| Rank | Supplier | Country | Composite | Propagated | Increase | Reason |
|---|---|---|---|---|---|---|
| 1 | S047 | Switzerland | 16.4 | 39.9 | **+23.4** | Depends on S009 (DR Congo, 75.0) |
| 2 | S050 | Germany | 25.2 | 46.1 | +20.9 | Depends on S024 (DR Congo, 77.3) |
| 3 | S089 | Switzerland | 5.8 | 23.1 | +17.4 | Depends on S049 (DR Congo, 73.2) |
| 4 | S041 | USA | 28.1 | 43.0 | +15.0 | Depends on S024 (DR Congo, 77.3) |

#### Hidden Vulnerabilities Detected

**Definition:** Suppliers with composite < 55 (MEDIUM or below) but propagated ≥ 55 (HIGH or above)
```
Found: 1 hidden vulnerability

S045 - China Superior Solutions
  Tier: 2
  Composite Risk: 45.2 [looks safe - MEDIUM]
  Propagated Risk: 57.0 [actually risky - HIGH]
  Hidden Vulnerability: +11.7 points
```

#### By-Tier Impact
```
Tier-1 (40 suppliers):
  • Average Composite: 41.19
  • Average Propagated: 43.83
  • Average Increase: +2.64 points

Tier-2 (40 suppliers):
  • Average Composite: 33.96
  • Average Propagated: 39.55
  • Average Increase: +5.59 points  ← Highest increase!

Tier-3 (40 suppliers):
  • Average Composite: 43.23
  • Average Propagated: 43.23
  • Average Increase: 0.00 points  ← No dependencies below
```

**Why Tier-2 has highest increase:** Direct exposure to risky Tier-3 raw material suppliers!

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
  • Total SPOFs detected: 17

  SPOFs by Tier:
    • Tier-1: 6 SPOFs
    • Tier-2: 2 SPOFs
    • Tier-3: 9 SPOFs

  SPOFs by Reason:
    • High risk (>60): 10 SPOFs
    • Only supplier for downstream: 7 SPOFs
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

**Found: 10 CRITICAL SPOFs**

All require immediate action (0-30 days):

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

#### SPOF Statistics
```
Total Suppliers: 120
Suppliers without backup: 87 (72.5%)
SPOFs detected: 17 (14.2%)

SPOF Detection Rate: 19.5% of no-backup suppliers are SPOFs

Most Impactful SPOF:
  S016 - United States Global Industries
  Affects 20 downstream suppliers
  €0.77M contract → €55.4M at risk
```

#### Business Recommendations Generated

**🔴 HIGH PRIORITY (0-30 days): 10 actions**
```
Qualify backup supplier for:
  • S017 (Plastic Resin)
  • S011 (Silicon Wafer)
  • S049 (Semiconductor Chip)
  • S055 (Connector Set)
  • S083 (Housing & Enclosure)
  • S085 (Assembled PCB Module)
  • S097 (Assembled PCB Module)
  • S103 (Battery Pack)
  • S108 (Display Panel Assembly)
  • S120 (Display Panel Assembly)
```

**🟡 MEDIUM PRIORITY (30-90 days): 2 actions**
```
Establish dual-sourcing for:
  • S040 (Aluminum Sheet)
  • S021 (Plastic Resin)
```

**🟢 LOW PRIORITY (90+ days): 5 actions**
```
Monitor and consider backup for:
  • S016 (Plastic Resin)
  • S034 (Silicon Wafer)
  • S008 (Aluminum Sheet)
  • S023 (Rare Earth Elements)
  • S032 (Lithium Compound)
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

### Visualization & Testing

| Technology | Version | Purpose |
|---|---|---|
| **Matplotlib** | 3.10+ | Static charts and visualizations |
| **Plotly** | 6.5+ | Interactive charts (future dashboard) |
| **Pytest** | 9.0+ | Unit testing framework |

### Future Stack (Roadmap)

- **Streamlit** - Interactive dashboard (Phase 4)
- **FastAPI** - REST API backend (Phase 5)
- **React** - Web frontend (Phase 5)
- **React Native** - Mobile app (Phase 6)

---

## 📁 Project Structure
```
suppliershield/
├── README.md                   # This file
├── LICENSE                     # MIT License
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variables template
│
├── src/                        # Core analytics engine
│   ├── __init__.py
│   ├── data/                   # Data generation & validation
│   │   ├── __init__.py
│   │   ├── generator.py        # Synthetic data generator (450 lines)
│   │   ├── loader.py           # Data validation module (200 lines)
│   │   └── schemas.py          # Schema definitions (150 lines)
│   ├── network/                # Graph construction
│   │   ├── __init__.py
│   │   ├── builder.py          # NetworkX graph builder (250 lines)
│   │   └── validator.py        # Network integrity checks (200 lines)
│   └── risk/                   # Risk analysis modules
│       ├── __init__.py
│       ├── config.py           # Risk weights & thresholds (80 lines)
│       ├── scorer.py           # Multi-dimensional risk scoring (300 lines)
│       ├── propagation.py      # Risk cascade algorithm (200 lines)
│       └── spof_detector.py    # SPOF detection & impact (250 lines)
│
├── data/
│   └── raw/                    # Generated CSV files
│       ├── suppliers.csv       # 120 suppliers
│       ├── dependencies.csv    # 237 edges
│       ├── country_risk.csv    # 14 countries
│       └── product_bom.csv     # 10 products
│
├── scripts/                    # Executable test scripts
│   ├── generate_data.py        # Data generation CLI
│   ├── validate_data.py        # Data validation CLI
│   ├── test_network.py         # Network construction test
│   ├── test_risk_scorer.py     # Risk scoring test
│   ├── test_risk_propagation.py # Risk propagation test
│   └── test_spof_detector.py   # SPOF detection test
│
├── tests/                      # Unit tests (Phase 6)
│   ├── __init__.py
│   ├── test_data_generator.py
│   ├── test_network_builder.py
│   ├── test_risk_scorer.py
│   └── test_propagation.py
│
├── notebooks/                  # Jupyter notebooks
│   └── 01_data_exploration.ipynb
│
└── docs/                       # Documentation
    ├── methodology.md
    ├── validation_report.md
    └── data_dictionary.md
```

**Total Code:** ~2,000 lines of Python across 15 modules

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
   lambda = (country_disaster_freq / 100) × 3
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

### Network Validation

All networks pass 4 integrity checks:
```
✓ Check 1: No cycles (DAG property)
✓ Check 2: Network connectivity (identifies orphans but allows them)
✓ Check 3: Correct tier flow (only T3→T2→T1 edges allowed)
✓ Check 4: No self-loops (supplier can't depend on itself)
```

### Risk Scoring Validation

**Weight Validation:**
```python
assert sum(RISK_WEIGHTS.values()) == 1.0
# geopolitical(0.30) + disaster(0.20) + financial(0.20) + 
# logistics(0.15) + concentration(0.15) = 1.00 ✓
```

**Output Range Validation:**
```python
assert all(0 <= score <= 100 for score in composite_risks)
# All 120 scores within valid range ✓
```

**Category Distribution Validation:**
```
Expected: Roughly normal distribution centered around 40-50
Actual:
  LOW (0-34): 44 suppliers (37%)
  MEDIUM (35-54): 56 suppliers (47%)
  HIGH (55-74): 17 suppliers (14%)
  CRITICAL (75-100): 3 suppliers (2.5%)
✓ Realistic distribution
```

### Risk Propagation Validation

**Algorithm Correctness - Manual Verification:**

**Test Case: 3-Node Chain**
```
S001 (Tier-3) → S041 (Tier-2) → S081 (Tier-1)

S001: composite = 59.0, propagated = 59.0 (no upstream)
S041: composite = 28.1
  upstream = [S001 (59.0), S014 (53.8)]
  avg_upstream = (59.0 + 53.8) / 2 = 56.4
  propagated = max(28.1, 28.1×0.6 + 56.4×0.4)
            = max(28.1, 16.86 + 22.56)
            = max(28.1, 39.42)
            = 39.42 ✓

Manual calculation matches system output ✓
```

**Monotonicity Validation:**
```python
assert all(propagated >= composite for all suppliers)
# Risk never decreases ✓
```

### SPOF Detection Validation

**Known SPOF Test:**
```
S016: has_backup = False, downstream_count = 20
Expected: Detected as SPOF
Actual: ✓ Detected, reason: "Only supplier for S042"

S089: has_backup = True, downstream_count = 0
Expected: NOT a SPOF (has backup)
Actual: ✓ Not detected

S024: has_backup = False, risk = 77.3
Expected: Detected as SPOF
Actual: ✓ Detected, reason: "High risk (77.3) with no backup"
```

**Impact Calculation Validation:**
```
S016 descendants: {S042, S053, S068, S069, ... 20 total}
Manual count: 20 ✓
System count: 20 ✓

Contract values:
S016: €0.77M
Sum of descendants: €54.63M
Total: €55.40M ✓
System total: €55.40M ✓
```

---

## 📈 Project Status & Roadmap

### Current Phase: Phase 2 Complete ✅

**Completed Phases:**

- ✅ **Phase 0 - Project Setup** (Week 1)
  - Git repository initialization
  - Virtual environment setup
  - Folder structure creation
  - README skeleton
  - MIT License

- ✅ **Phase 1 - Data Layer** (Weeks 2-3)
  - Synthetic data generator (400+ lines)
  - Data validation module
  - Country risk data (14 countries)
  - Schema definitions
  - 120 suppliers, 237 dependencies, 10 products

- ✅ **Phase 2 - Network & Risk Engine** (Weeks 4-5)
  - Network graph construction (NetworkX)
  - Network validation (4 checks)
  - Five-dimension risk scoring
  - Risk propagation algorithm
  - SPOF detection with impact analysis

### Upcoming Phases

**🔄 Phase 3 - Disruption Simulation** (Weeks 6-7)
- Monte Carlo disruption simulator (1,000-10,000 iterations)
- Three scenario types:
  - Single-node knockout
  - Regional disruption
  - Correlated failure
- Sensitivity analysis (criticality ranking)
- BOM-to-supplier impact tracing

**🔄 Phase 4 - Recommendations & BOM** (Week 8)
- Rule-based recommendation engine
- BOM impact tracer
- Scenario comparison

**🔄 Phase 5 - Streamlit Dashboard** (Weeks 9-10)
- 5 interactive pages:
  - Network Overview
  - Risk Rankings
  - What-If Simulator
  - Sensitivity Analysis
  - Recommendations
- Interactive network visualization (pyvis/plotly)
- Export to PDF/CSV

**🔄 Phase 6 - Testing & Polish** (Weeks 11-12)
- Unit tests (80%+ coverage)
- Integration tests
- Documentation completion
- Demo video
- v1.0 release

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
- Quantify revenue-at-risk from supplier disruptions
- Detect hidden vulnerabilities in multi-tier dependencies
- Monitor concentration risk by region/country

**Value Delivered:**
- 1 hidden vulnerability revealed (S045: looked safe, actually high-risk)
- Regional concentration quantified (e.g., 9/10 critical SPOFs in DR Congo)
- Propagated risk increases averaged +2.74 points across 47 suppliers

### For Supply Chain Directors

**Problem:** "Where should we invest in supply chain resilience?"

**Solution:**
- Data-driven supplier diversification strategy
- SPOF elimination roadmap with timelines
- Network resilience metrics and KPIs

**Value Delivered:**
- 72x impact multiplier discovered (S016: €0.77M → €55.4M at risk)
- Tier-2 identified as highest-risk tier (avg +5.59 point increase from propagation)
- Clear action plan: 10 high-priority, 2 medium-priority, 5 low-priority actions

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

- Portfolio project demonstrating supply chain analytics and graph theory
- Synthetic data methodology based on World Bank and ND-GAIN indices
- Designed for the Venlo-Limburg logistics and manufacturing industry
- Built with guidance on best practices for procurement risk management

---

## ⚠️ Important Notes

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
- Algorithm design and implementation
- Data validation and quality assurance
- Python software engineering best practices

---

**Last Updated:** February 2026  
**Version:** 2.0 (Phase 2 Complete)  
**Status:** Active Development