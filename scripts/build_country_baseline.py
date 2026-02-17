#!/usr/bin/env python3
"""
Build country risk baseline from source datasets.

Reads 4 source CSVs (WGI political stability, INFORM natural hazard,
LPI logistics scores, trade restriction counts), normalizes each to
0-100, merges on country_code, fills missing values with sub-regional
medians, and outputs a unified baseline CSV.

Usage:
    python scripts/build_country_baseline.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import pycountry
except ImportError:
    print("ERROR: pycountry is required. Install with: pip install pycountry")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = PROJECT_ROOT / "data" / "sources"
BASELINE_DIR = PROJECT_ROOT / "data" / "baseline"

WGI_PATH = SOURCES_DIR / "wgi_political_stability.csv"
INFORM_PATH = SOURCES_DIR / "inform_natural_hazard.csv"
LPI_PATH = SOURCES_DIR / "lpi_scores.csv"
TRADE_PATH = SOURCES_DIR / "trade_restrictions.csv"
OUTPUT_PATH = BASELINE_DIR / "country_risk_baseline.csv"


# ---------------------------------------------------------------------------
# UN sub-region mapping via pycountry + manual overrides
# ---------------------------------------------------------------------------
# ISO 3166-1 numeric -> UN sub-region name
# We build this from pycountry's subdivision data where possible,
# but many countries need a manual mapping.

_SUBREGION_MAP = {
    # Southern Asia
    "AF": "Southern Asia", "BD": "Southern Asia", "BT": "Southern Asia",
    "IN": "Southern Asia", "IR": "Southern Asia", "MV": "Southern Asia",
    "NP": "Southern Asia", "PK": "Southern Asia", "LK": "Southern Asia",
    # South-Eastern Asia
    "BN": "South-Eastern Asia", "KH": "South-Eastern Asia",
    "ID": "South-Eastern Asia", "LA": "South-Eastern Asia",
    "MY": "South-Eastern Asia", "MM": "South-Eastern Asia",
    "PH": "South-Eastern Asia", "SG": "South-Eastern Asia",
    "TH": "South-Eastern Asia", "TL": "South-Eastern Asia",
    "VN": "South-Eastern Asia",
    # Eastern Asia
    "CN": "Eastern Asia", "JP": "Eastern Asia", "KP": "Eastern Asia",
    "KR": "Eastern Asia", "MN": "Eastern Asia", "TW": "Eastern Asia",
    # Central Asia
    "KZ": "Central Asia", "KG": "Central Asia", "TJ": "Central Asia",
    "TM": "Central Asia", "UZ": "Central Asia",
    # Western Asia
    "AM": "Western Asia", "AZ": "Western Asia", "BH": "Western Asia",
    "CY": "Western Asia", "GE": "Western Asia", "IQ": "Western Asia",
    "IL": "Western Asia", "JO": "Western Asia", "KW": "Western Asia",
    "LB": "Western Asia", "OM": "Western Asia", "QA": "Western Asia",
    "SA": "Western Asia", "SY": "Western Asia", "TR": "Western Asia",
    "AE": "Western Asia", "YE": "Western Asia",
    # Northern Europe
    "DK": "Northern Europe", "EE": "Northern Europe", "FI": "Northern Europe",
    "IS": "Northern Europe", "IE": "Northern Europe", "LV": "Northern Europe",
    "LT": "Northern Europe", "NO": "Northern Europe", "SE": "Northern Europe",
    "GB": "Northern Europe",
    # Western Europe
    "AT": "Western Europe", "BE": "Western Europe", "FR": "Western Europe",
    "DE": "Western Europe", "LI": "Western Europe", "LU": "Western Europe",
    "MC": "Western Europe", "NL": "Western Europe", "CH": "Western Europe",
    # Southern Europe
    "AL": "Southern Europe", "AD": "Southern Europe", "BA": "Southern Europe",
    "HR": "Southern Europe", "GR": "Southern Europe", "IT": "Southern Europe",
    "MT": "Southern Europe", "ME": "Southern Europe", "MK": "Southern Europe",
    "PT": "Southern Europe", "SM": "Southern Europe", "RS": "Southern Europe",
    "SI": "Southern Europe", "ES": "Southern Europe",
    # Eastern Europe
    "BY": "Eastern Europe", "BG": "Eastern Europe", "CZ": "Eastern Europe",
    "HU": "Eastern Europe", "PL": "Eastern Europe", "MD": "Eastern Europe",
    "RO": "Eastern Europe", "RU": "Eastern Europe", "SK": "Eastern Europe",
    "UA": "Eastern Europe",
    # Northern Africa
    "DZ": "Northern Africa", "EG": "Northern Africa", "LY": "Northern Africa",
    "MA": "Northern Africa", "SD": "Northern Africa", "TN": "Northern Africa",
    # Western Africa
    "BJ": "Western Africa", "BF": "Western Africa", "CV": "Western Africa",
    "CI": "Western Africa", "GM": "Western Africa", "GH": "Western Africa",
    "GN": "Western Africa", "GW": "Western Africa", "LR": "Western Africa",
    "ML": "Western Africa", "MR": "Western Africa", "NE": "Western Africa",
    "NG": "Western Africa", "SN": "Western Africa", "SL": "Western Africa",
    "TG": "Western Africa",
    # Eastern Africa
    "BI": "Eastern Africa", "KM": "Eastern Africa", "DJ": "Eastern Africa",
    "ER": "Eastern Africa", "ET": "Eastern Africa", "KE": "Eastern Africa",
    "MG": "Eastern Africa", "MW": "Eastern Africa", "MU": "Eastern Africa",
    "MZ": "Eastern Africa", "RW": "Eastern Africa", "SC": "Eastern Africa",
    "SO": "Eastern Africa", "SS": "Eastern Africa", "TZ": "Eastern Africa",
    "UG": "Eastern Africa", "ZM": "Eastern Africa", "ZW": "Eastern Africa",
    # Middle Africa
    "AO": "Middle Africa", "CM": "Middle Africa", "CF": "Middle Africa",
    "TD": "Middle Africa", "CG": "Middle Africa", "CD": "Middle Africa",
    "GQ": "Middle Africa", "GA": "Middle Africa", "ST": "Middle Africa",
    # Southern Africa
    "BW": "Southern Africa", "SZ": "Southern Africa", "LS": "Southern Africa",
    "NA": "Southern Africa", "ZA": "Southern Africa",
    # Northern America
    "CA": "Northern America", "US": "Northern America", "MX": "Northern America",
    # Central America
    "BZ": "Central America", "CR": "Central America", "SV": "Central America",
    "GT": "Central America", "HN": "Central America", "NI": "Central America",
    "PA": "Central America",
    # Caribbean
    "AG": "Caribbean", "BS": "Caribbean", "BB": "Caribbean", "CU": "Caribbean",
    "DM": "Caribbean", "DO": "Caribbean", "GD": "Caribbean", "HT": "Caribbean",
    "JM": "Caribbean", "KN": "Caribbean", "LC": "Caribbean", "VC": "Caribbean",
    "TT": "Caribbean",
    # South America
    "AR": "South America", "BO": "South America", "BR": "South America",
    "CL": "South America", "CO": "South America", "EC": "South America",
    "GY": "South America", "PY": "South America", "PE": "South America",
    "SR": "South America", "UY": "South America", "VE": "South America",
    # Australia and New Zealand
    "AU": "Australia and New Zealand", "NZ": "Australia and New Zealand",
    # Melanesia
    "FJ": "Melanesia", "PG": "Melanesia", "SB": "Melanesia", "VU": "Melanesia",
    # Micronesia
    "KI": "Micronesia", "MH": "Micronesia", "FM": "Micronesia",
    "NR": "Micronesia", "PW": "Micronesia",
    # Polynesia
    "WS": "Polynesia", "TO": "Polynesia", "TV": "Polynesia",
}


def get_subregion(code: str) -> str:
    """Return UN sub-region for an ISO alpha-2 country code."""
    return _SUBREGION_MAP.get(code, "Unknown")


def get_canonical_name(code: str, fallback: str) -> str:
    """Return pycountry canonical name, falling back to the source name."""
    try:
        country = pycountry.countries.get(alpha_2=code)
        if country:
            return country.name
    except Exception:
        pass
    return fallback


def normalize_political_stability(wgi_value: float) -> float:
    """Convert WGI [-2.5, +2.5] to risk 0-100 (higher = more risk)."""
    return (2.5 - wgi_value) / 5.0 * 100.0


def normalize_natural_hazard(inform_value: float) -> float:
    """Convert INFORM [0, 10] to 0-100."""
    return inform_value / 10.0 * 100.0


def normalize_logistics(lpi_value: float) -> float:
    """Convert LPI [1, 5] to 0-100 (higher = better logistics)."""
    return (lpi_value - 1.0) / 4.0 * 100.0


def normalize_trade_restrictions(series: pd.Series) -> pd.Series:
    """Convert raw intervention counts to percentile rank 0-100."""
    return series.rank(pct=True) * 100.0


def fill_with_subregion_median(
    merged: pd.DataFrame, col: str, subregions: pd.Series
) -> pd.DataFrame:
    """Fill NaN values in col with the median of the country's sub-region."""
    merged["_subregion"] = subregions
    region_medians = merged.groupby("_subregion")[col].median()

    mask = merged[col].isna()
    if mask.any():
        filled_count = 0
        for idx in merged[mask].index:
            region = merged.loc[idx, "_subregion"]
            median_val = region_medians.get(region, np.nan)
            if pd.isna(median_val):
                median_val = 50.0  # global fallback
            merged.loc[idx, col] = median_val
            filled_count += 1
        if filled_count > 0:
            print(f"  Filled {filled_count} missing values in '{col}' "
                  f"using sub-region medians")

    merged.drop(columns=["_subregion"], inplace=True)
    return merged


def main():
    print("=" * 65)
    print("SupplierShield Country Risk Baseline Builder")
    print("=" * 65)

    # ------------------------------------------------------------------
    # Load source CSVs
    # ------------------------------------------------------------------
    print("\n[1/5] Loading source datasets...")

    wgi = pd.read_csv(WGI_PATH)
    inform = pd.read_csv(INFORM_PATH)
    lpi = pd.read_csv(LPI_PATH)
    trade = pd.read_csv(TRADE_PATH)

    print(f"  WGI Political Stability:  {len(wgi):>4} countries")
    print(f"  INFORM Natural Hazard:    {len(inform):>4} countries")
    print(f"  LPI Logistics:            {len(lpi):>4} countries")
    print(f"  Trade Restrictions:       {len(trade):>4} countries")

    # ------------------------------------------------------------------
    # Normalize each dimension
    # ------------------------------------------------------------------
    print("\n[2/5] Normalizing dimensions to 0-100 scale...")

    wgi["political_stability"] = wgi["wgi_political_stability"].apply(
        normalize_political_stability
    )
    inform["natural_disaster_freq"] = inform["inform_natural_hazard"].apply(
        normalize_natural_hazard
    )
    lpi["logistics_performance"] = lpi["lpi_score"].apply(
        normalize_logistics
    )
    trade["trade_restriction_risk"] = normalize_trade_restrictions(
        trade["trade_restriction_count"]
    )

    print("  political_stability:     (2.5 - WGI) / 5.0 * 100  "
          "[higher = more risk]")
    print("  natural_disaster_freq:   INFORM / 10 * 100")
    print("  logistics_performance:   (LPI - 1) / 4 * 100  "
          "[higher = better]")
    print("  trade_restriction_risk:  percentile rank * 100")

    # ------------------------------------------------------------------
    # Merge on country_code
    # ------------------------------------------------------------------
    print("\n[3/5] Merging datasets...")

    # Build the master country list from the union of all sources (drop NaN codes)
    all_codes = sorted(set(
        c for c in (
            wgi["country_code"].tolist()
            + inform["country_code"].tolist()
            + lpi["country_code"].tolist()
            + trade["country_code"].tolist()
        ) if isinstance(c, str) and len(c) == 2
    ))

    # Collect country names from sources (prefer WGI, then others)
    name_lookup = {}
    for df in [trade, lpi, inform, wgi]:  # last wins
        for _, row in df.iterrows():
            name_lookup[row["country_code"]] = row["country_name"]

    master = pd.DataFrame({
        "country_code": all_codes,
        "country_name_source": [name_lookup.get(c, c) for c in all_codes],
    })

    # Merge each dimension
    merged = master.merge(
        wgi[["country_code", "political_stability"]],
        on="country_code", how="left"
    ).merge(
        inform[["country_code", "natural_disaster_freq"]],
        on="country_code", how="left"
    ).merge(
        lpi[["country_code", "logistics_performance"]],
        on="country_code", how="left"
    ).merge(
        trade[["country_code", "trade_restriction_risk"]],
        on="country_code", how="left"
    )

    print(f"  Master country list: {len(merged)} countries")

    missing_counts = merged[
        ["political_stability", "natural_disaster_freq",
         "logistics_performance", "trade_restriction_risk"]
    ].isna().sum()
    for col, count in missing_counts.items():
        if count > 0:
            print(f"  Missing in {col}: {count}")

    # ------------------------------------------------------------------
    # Fill missing values with sub-region medians
    # ------------------------------------------------------------------
    print("\n[4/5] Filling missing values with sub-region medians...")

    subregions = merged["country_code"].map(get_subregion)

    for col in ["political_stability", "natural_disaster_freq",
                "logistics_performance", "trade_restriction_risk"]:
        merged = fill_with_subregion_median(merged, col, subregions)

    # ------------------------------------------------------------------
    # Finalize and output
    # ------------------------------------------------------------------
    print("\n[5/5] Finalizing baseline...")

    # Use pycountry for canonical names
    merged["country"] = merged.apply(
        lambda row: get_canonical_name(
            row["country_code"], row["country_name_source"]
        ),
        axis=1,
    )

    # Clamp to 0-100 and round to integers
    for col in ["political_stability", "natural_disaster_freq",
                "logistics_performance", "trade_restriction_risk"]:
        merged[col] = merged[col].clip(0, 100).round(0).astype(int)

    # Select and order output columns
    output = merged[[
        "country", "country_code",
        "political_stability", "natural_disaster_freq",
        "logistics_performance", "trade_restriction_risk",
    ]].sort_values("country_code").reset_index(drop=True)

    # Write CSV
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)

    print(f"\n  Output: {OUTPUT_PATH}")
    print(f"  Countries: {len(output)}")
    print(f"  Columns: {', '.join(output.columns)}")

    # Summary statistics
    print("\n  Dimension statistics (0-100 scale):")
    for col in ["political_stability", "natural_disaster_freq",
                "logistics_performance", "trade_restriction_risk"]:
        vals = output[col]
        print(f"    {col:30s}  "
              f"min={vals.min():3d}  median={int(vals.median()):3d}  "
              f"max={vals.max():3d}")

    # Top/bottom examples
    print("\n  Highest political risk:")
    top_risk = output.nlargest(5, "political_stability")
    for _, row in top_risk.iterrows():
        print(f"    {row['country']:30s} ({row['country_code']})  "
              f"score={row['political_stability']}")

    print("\n  Lowest political risk:")
    low_risk = output.nsmallest(5, "political_stability")
    for _, row in low_risk.iterrows():
        print(f"    {row['country']:30s} ({row['country_code']})  "
              f"score={row['political_stability']}")

    print("\n" + "=" * 65)
    print("Baseline build complete.")
    print("=" * 65)


if __name__ == "__main__":
    main()
