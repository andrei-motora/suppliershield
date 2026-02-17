"""Tests for the country risk baseline merge logic."""

import pandas as pd
import pytest

from src.data.baseline import load_baseline, merge_country_risk


@pytest.fixture
def baseline():
    return load_baseline()


@pytest.fixture
def user_override():
    """A small user-uploaded country risk CSV (overrides for CN and DE)."""
    return pd.DataFrame({
        "country": ["China", "Germany"],
        "country_code": ["CN", "DE"],
        "political_stability": [45, 15],
        "natural_disaster_freq": [55, 20],
        "logistics_performance": [75, 90],
        "trade_restriction_risk": [40, 10],
    })


def test_baseline_loads(baseline):
    """Baseline should load ~193 countries with all required columns."""
    assert len(baseline) >= 190
    for col in ["country", "country_code", "political_stability",
                "natural_disaster_freq", "logistics_performance",
                "trade_restriction_risk"]:
        assert col in baseline.columns


def test_baseline_values_in_range(baseline):
    """All numeric columns should be in 0-100."""
    for col in ["political_stability", "natural_disaster_freq",
                "logistics_performance", "trade_restriction_risk"]:
        assert baseline[col].min() >= 0
        assert baseline[col].max() <= 100


def test_merge_no_user_data(baseline):
    """When no user data is provided, return the full baseline."""
    result = merge_country_risk(baseline, None)
    assert len(result) == len(baseline)
    assert set(result["country_code"]) == set(baseline["country_code"])


def test_merge_empty_user_data(baseline):
    """Empty user DataFrame should return full baseline."""
    empty = pd.DataFrame(columns=baseline.columns)
    result = merge_country_risk(baseline, empty)
    assert len(result) == len(baseline)


def test_merge_partial_overlap(baseline, user_override):
    """User overrides for CN and DE; baseline fills remaining countries."""
    result = merge_country_risk(baseline, user_override)
    # Total should be baseline - 2 overridden + 2 user rows = same as baseline
    assert len(result) == len(baseline)

    # User values should win for CN
    cn_row = result[result["country_code"] == "CN"].iloc[0]
    assert cn_row["political_stability"] == 45
    assert cn_row["logistics_performance"] == 75

    # DE should also have user values
    de_row = result[result["country_code"] == "DE"].iloc[0]
    assert de_row["political_stability"] == 15

    # A country not in user override should have baseline values
    jp_rows = result[result["country_code"] == "JP"]
    assert len(jp_rows) == 1
    bl_jp = baseline[baseline["country_code"] == "JP"].iloc[0]
    assert jp_rows.iloc[0]["political_stability"] == bl_jp["political_stability"]


def test_merge_full_override(baseline):
    """When user provides all countries, only user data is used."""
    # Create user data for all baseline countries with all values set to 50
    full_override = baseline.copy()
    full_override["political_stability"] = 50
    result = merge_country_risk(baseline, full_override)
    assert len(result) == len(baseline)
    assert (result["political_stability"] == 50).all()
