# Country Risk Baseline - Data Sources & Methodology

## Source Datasets

### 1. World Bank WGI Political Stability (2023)
- **File**: `data/sources/wgi_political_stability.csv`
- **Source**: World Bank Worldwide Governance Indicators
- **URL**: https://info.worldbank.org/governance/wgi/
- **Indicator**: Political Stability and Absence of Violence/Terrorism
- **Original scale**: -2.5 (most unstable) to +2.5 (most stable)
- **Normalization**: `political_stability = (2.5 - wgi_value) / 5.0 * 100`
- **Interpretation**: Higher score = higher political risk (0-100)

### 2. INFORM Risk Index Natural Hazard (2024)
- **File**: `data/sources/inform_natural_hazard.csv`
- **Source**: INFORM Risk Index (EC Joint Research Centre / OCHA)
- **URL**: https://drmkc.jrc.ec.europa.eu/inform-index
- **Indicator**: Natural Hazard exposure composite score
- **Original scale**: 0 (minimal exposure) to 10 (extreme exposure)
- **Normalization**: `natural_disaster_freq = inform_value / 10 * 100`
- **Interpretation**: Higher score = greater natural hazard exposure (0-100)

### 3. World Bank Logistics Performance Index (2023)
- **File**: `data/sources/lpi_scores.csv`
- **Source**: World Bank LPI
- **URL**: https://lpi.worldbank.org/
- **Indicator**: Overall LPI aggregate score
- **Original scale**: 1 (worst) to 5 (best)
- **Normalization**: `logistics_performance = (lpi_value - 1) / 4 * 100`
- **Interpretation**: Higher score = better logistics capability (0-100)

### 4. Global Trade Alert Intervention Counts (2023)
- **File**: `data/sources/trade_restrictions.csv`
- **Source**: Global Trade Alert (St. Gallen Endowment for Prosperity Through Trade)
- **URL**: https://www.globaltradealert.org/
- **Indicator**: Cumulative count of trade-distorting interventions
- **Original scale**: Raw count of interventions
- **Normalization**: Percentile rank scaled to 0-100
- **Interpretation**: Higher score = more trade restrictions relative to peers (0-100)

## Missing Data Handling

When a country is present in some source datasets but absent from others:

1. **Sub-region median**: The missing value is filled with the median of all countries in the same UN M49 sub-region (e.g., "Southern Asia", "Western Europe")
2. **Global fallback**: If no countries from the sub-region have data, a default value of 50 (midpoint) is used

Country names are canonicalized using the `pycountry` library (ISO 3166-1). If a country code is not recognized by pycountry (e.g., TW for Taiwan), the name from the source file is retained.

## Output

- **File**: `data/baseline/country_risk_baseline.csv`
- **Columns**: `country`, `country_code`, `political_stability`, `natural_disaster_freq`, `logistics_performance`, `trade_restriction_risk`
- **All values**: Integers 0-100

## Important Disclaimer

The values in the source CSVs are **representative approximations** based on publicly available data and known geopolitical realities. They are intended for demonstration and development purposes within the SupplierShield platform. They should not be cited as authoritative data. For production use, obtain official datasets directly from the sources listed above and replace the source CSVs accordingly.

## Build Command

```bash
python scripts/build_country_baseline.py
```
