"""
Country risk baseline utilities for SupplierShield.

Provides load_baseline() to load the built-in 195-country baseline,
and merge_country_risk() to combine baseline with user-uploaded overrides.
"""

import pandas as pd
from pathlib import Path


# Resolve baseline path relative to this file: src/data/baseline.py -> data/baseline/
_BASELINE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "baseline"
BASELINE_CSV = _BASELINE_DIR / "country_risk_baseline.csv"


def load_baseline() -> pd.DataFrame:
    """
    Load the built-in country risk baseline (~195 countries).

    Returns:
        DataFrame with columns: country, country_code, political_stability,
        natural_disaster_freq, logistics_performance, trade_restriction_risk
    """
    if not BASELINE_CSV.exists():
        raise FileNotFoundError(
            f"Country risk baseline not found at {BASELINE_CSV}. "
            "Run `python scripts/build_country_baseline.py` to generate it."
        )
    return pd.read_csv(BASELINE_CSV)


def merge_country_risk(
    baseline_df: pd.DataFrame,
    user_override_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    Merge user-uploaded country risk data with the built-in baseline.

    User rows take priority for matching country_codes.
    Baseline rows fill in all remaining countries.

    Args:
        baseline_df: The full baseline DataFrame (~195 rows)
        user_override_df: User-uploaded country_risk DataFrame, or None

    Returns:
        Merged DataFrame with user overrides applied on top of baseline.
    """
    if user_override_df is None or user_override_df.empty:
        return baseline_df.copy()

    override_codes = set(user_override_df["country_code"])
    baseline_only = baseline_df[~baseline_df["country_code"].isin(override_codes)]
    return pd.concat([user_override_df, baseline_only], ignore_index=True)
