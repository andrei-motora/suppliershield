"""
Risk scoring configuration for SupplierShield.

This module contains all weights, thresholds, and constants used in risk calculation.
"""

from typing import Dict


# Risk dimension weights (must sum to 1.0)
RISK_WEIGHTS: Dict[str, float] = {
    'geopolitical': 0.30,      # 30% - Political stability
    'natural_disaster': 0.20,  # 20% - Natural disaster frequency
    'financial': 0.20,         # 20% - Financial health
    'logistics': 0.15,         # 15% - Logistics performance
    'concentration': 0.15      # 15% - Supplier concentration
}

# Verify weights sum to 1.0
assert abs(sum(RISK_WEIGHTS.values()) - 1.0) < 0.001, "Risk weights must sum to 1.0"


# Risk categories and thresholds
RISK_CATEGORIES = {
    'LOW': (0, 34),        # 0-34: Low risk
    'MEDIUM': (35, 54),    # 35-54: Medium risk
    'HIGH': (55, 74),      # 55-74: High risk
    'CRITICAL': (75, 100)  # 75-100: Critical risk
}


def get_risk_category(score: float) -> str:
    """
    Get the risk category for a given score.
    
    Args:
        score: Risk score (0-100)
        
    Returns:
        Category name: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'
    """
    if score <= 34:
        return 'LOW'
    elif score <= 54:
        return 'MEDIUM'
    elif score <= 74:
        return 'HIGH'
    else:
        return 'CRITICAL'


# Color codes for visualization (matches project design system)
RISK_COLORS = {
    'LOW': '#22c55e',       # Green
    'MEDIUM': '#eab308',    # Yellow
    'HIGH': '#f97316',      # Orange
    'CRITICAL': '#ef4444'   # Red
}


# Concentration risk thresholds
# How many incoming suppliers determine concentration risk
CONCENTRATION_THRESHOLDS = {
    'tier_1_high_risk': 75,   # Tier-1 with ≤1 supplier: very risky
    'tier_2_3_high_risk': 60, # Tier-2/3 with ≤1 supplier: risky
    'base_risk': 10,          # Minimum concentration risk
    'reduction_per_supplier': 15  # Risk reduction per additional supplier
}