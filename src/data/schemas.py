"""
Data schemas for SupplierShield.

This module defines the structure and validation rules for all data files.
Each schema is a Python dictionary that describes what columns the CSV should have.
"""

from typing import Dict, List, Any


# Schema for suppliers.csv
SUPPLIER_SCHEMA: Dict[str, Any] = {
    'id': str,              # Unique supplier ID (e.g., "S001")
    'name': str,            # Supplier company name
    'tier': int,            # Supply chain tier (1, 2, or 3)
    'component': str,       # What this supplier provides
    'country': str,         # Country name
    'country_code': str,    # ISO 2-letter code (e.g., "CN")
    'region': str,          # Geographic region
    'contract_value_eur_m': float,  # Annual contract value in millions of euros
    'lead_time_days': int,  # How many days to deliver
    'financial_health': int,  # Score 0-100 (higher = healthier)
    'past_disruptions': int,  # Number of disruptions in past 5 years
    'has_backup': bool      # Whether a backup supplier exists
}

# Schema for dependencies.csv
DEPENDENCY_SCHEMA: Dict[str, Any] = {
    'source_id': str,       # Supplier providing the input (e.g., "S020")
    'target_id': str,       # Supplier receiving the input (e.g., "S005")
    'dependency_weight': int  # Percentage of component sourced (0-100)
}

# Schema for country_risk.csv
COUNTRY_RISK_SCHEMA: Dict[str, Any] = {
    'country': str,
    'country_code': str,
    'political_stability': int,      # 0-100 (higher = more risk)
    'natural_disaster_freq': int,    # 0-100 (higher = more risk)
    'logistics_performance': int,    # 0-100 (higher = better!)
    'trade_restriction_risk': int    # 0-100 (higher = more risk)
}

# Schema for product_bom.csv
PRODUCT_BOM_SCHEMA: Dict[str, Any] = {
    'product_id': str,              # Product identifier (e.g., "P001")
    'product_name': str,            # Product name
    'annual_revenue_eur_m': float,  # Annual revenue in millions
    'component_supplier_ids': str   # Comma-separated supplier IDs
}


# Lists of realistic data for generation
TIER_1_COMPONENTS: List[str] = [
    "Assembled PCB Module",
    "Final Electronics Assembly",
    "Power Supply Unit",
    "Display Panel Assembly",
    "Battery Pack",
    "Sensor Module",
    "Control Unit",
    "Housing & Enclosure"
]

TIER_2_COMPONENTS: List[str] = [
    "Semiconductor Chip",
    "Capacitor Array",
    "LED Component",
    "Connector Set",
    "Resistor Network",
    "Microcontroller",
    "Memory Module",
    "Circuit Board"
]

TIER_3_COMPONENTS: List[str] = [
    "Copper Wire",
    "Silicon Wafer",
    "Rare Earth Elements",
    "Plastic Resin",
    "Aluminum Sheet",
    "Glass Substrate",
    "Lithium Compound",
    "Steel Alloy"
]

# Geographic regions
REGIONS: Dict[str, str] = {
    'CN': 'Asia-Pacific',
    'MY': 'Asia-Pacific',
    'TW': 'Asia-Pacific',
    'VN': 'Asia-Pacific',
    'TH': 'Asia-Pacific',
    'JP': 'Asia-Pacific',
    'KR': 'Asia-Pacific',
    'IN': 'Asia-Pacific',
    'DE': 'Europe',
    'NL': 'Europe',
    'PL': 'Europe',
    'CH': 'Europe',
    'US': 'North America',
    'CD': 'Africa'
}