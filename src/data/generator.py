"""
Synthetic data generator for SupplierShield.

This module creates realistic fake supplier data for testing and demonstration.
All data is randomly generated but follows real-world patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import random

from .schemas import (
    TIER_1_COMPONENTS,
    TIER_2_COMPONENTS,
    TIER_3_COMPONENTS,
    REGIONS
)


class SupplierDataGenerator:
    """
    Generates synthetic supplier network data.
    
    This class creates CSV files with realistic supplier data, dependencies,
    and product BOMs. All generation uses a random seed for reproducibility.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the generator.
        
        Args:
            seed: Random seed for reproducible generation (default: 42)
        """
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        # Load country risk data (we'll use this to assign suppliers to countries)
        self.country_risk = None
        
    def load_country_risk(self, filepath: Path) -> None:
        """
        Load country risk data from CSV.
        
        Args:
            filepath: Path to country_risk.csv
        """
        self.country_risk = pd.read_csv(filepath)
        print(f"[OK] Loaded {len(self.country_risk)} countries")
        
    def generate_suppliers(self, 
                          n_tier1: int = 40,
                          n_tier2: int = 40,
                          n_tier3: int = 40) -> pd.DataFrame:
        """
        Generate supplier master data.
        
        Args:
            n_tier1: Number of Tier-1 suppliers
            n_tier2: Number of Tier-2 suppliers
            n_tier3: Number of Tier-3 suppliers
            
        Returns:
            DataFrame with all supplier data
        """
        if self.country_risk is None:
            raise ValueError("Must load country risk data first!")
        
        suppliers = []
        supplier_id = 1
        
        # Generate Tier-3 suppliers (raw materials)
        print(f"Generating {n_tier3} Tier-3 suppliers...")
        for i in range(n_tier3):
            supplier = self._create_supplier(
                supplier_id=supplier_id,
                tier=3,
                component=random.choice(TIER_3_COMPONENTS)
            )
            suppliers.append(supplier)
            supplier_id += 1
        
        # Generate Tier-2 suppliers (components)
        print(f"Generating {n_tier2} Tier-2 suppliers...")
        for i in range(n_tier2):
            supplier = self._create_supplier(
                supplier_id=supplier_id,
                tier=2,
                component=random.choice(TIER_2_COMPONENTS)
            )
            suppliers.append(supplier)
            supplier_id += 1
        
        # Generate Tier-1 suppliers (assemblies)
        print(f"Generating {n_tier1} Tier-1 suppliers...")
        for i in range(n_tier1):
            supplier = self._create_supplier(
                supplier_id=supplier_id,
                tier=1,
                component=random.choice(TIER_1_COMPONENTS)
            )
            suppliers.append(supplier)
            supplier_id += 1
        
        df = pd.DataFrame(suppliers)
        print(f"[OK] Generated {len(df)} total suppliers")
        return df
    
    def _create_supplier(self, supplier_id: int, tier: int, component: str) -> dict:
        """
        Create a single supplier record.
        
        Args:
            supplier_id: Unique ID number
            tier: Supply chain tier (1, 2, or 3)
            component: What this supplier provides
            
        Returns:
            Dictionary with all supplier fields
        """
        # Pick a random country
        country_row = self.country_risk.sample(n=1).iloc[0]
        country = country_row['country']
        country_code = country_row['country_code']
        region = REGIONS[country_code]
        
        # Generate company name
        prefixes = ['Global', 'Precision', 'Advanced', 'International', 'Superior']
        suffixes = ['Industries', 'Manufacturing', 'Systems', 'Technologies', 'Solutions']
        name = f"{country} {random.choice(prefixes)} {random.choice(suffixes)}"
        
        # Contract value: Tier-1 highest, Tier-3 lowest
        if tier == 1:
            contract_value = round(np.random.uniform(1.5, 5.0), 2)
        elif tier == 2:
            contract_value = round(np.random.uniform(0.5, 2.5), 2)
        else:  # tier == 3
            contract_value = round(np.random.uniform(0.2, 1.2), 2)
        
        # Lead time: inversely related to tier (Tier-3 takes longer)
        if tier == 1:
            lead_time = int(np.random.uniform(10, 25))
        elif tier == 2:
            lead_time = int(np.random.uniform(20, 40))
        else:  # tier == 3
            lead_time = int(np.random.uniform(30, 60))
        
        # Financial health: somewhat correlated with country stability
        base_health = 100 - country_row['political_stability']
        financial_health = int(np.clip(
            np.random.normal(base_health, 20),
            0, 100
        ))
        
        # Past disruptions: correlated with natural disaster frequency
        disruption_prob = country_row['natural_disaster_freq'] / 100
        past_disruptions = np.random.poisson(disruption_prob * 3)
        
        # Has backup: ~30% of suppliers have backups
        has_backup = np.random.random() < 0.30
        
        return {
            'id': f"S{supplier_id:03d}",
            'name': name,
            'tier': tier,
            'component': component,
            'country': country,
            'country_code': country_code,
            'region': region,
            'contract_value_eur_m': contract_value,
            'lead_time_days': lead_time,
            'financial_health': financial_health,
            'past_disruptions': past_disruptions,
            'has_backup': has_backup
        }
    
    def generate_dependencies(self, suppliers_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate supplier-to-supplier dependencies.
        
        Creates edges showing which suppliers feed into which others.
        Tier-3 feeds Tier-2, Tier-2 feeds Tier-1.
        
        Args:
            suppliers_df: DataFrame with supplier data
            
        Returns:
            DataFrame with dependency edges
        """
        print("Generating supplier dependencies...")
        
        tier1 = suppliers_df[suppliers_df['tier'] == 1]
        tier2 = suppliers_df[suppliers_df['tier'] == 2]
        tier3 = suppliers_df[suppliers_df['tier'] == 3]
        
        dependencies = []
        
        # Tier-3 → Tier-2 connections
        for _, t2_supplier in tier2.iterrows():
            # Each Tier-2 gets 1-3 Tier-3 suppliers
            n_suppliers = np.random.randint(1, 4)
            t3_sources = tier3.sample(n=min(n_suppliers, len(tier3)))
            
            for _, t3_supplier in t3_sources.iterrows():
                # Dependency weight: how much of this component comes from this source
                weight = np.random.randint(30, 100)
                
                dependencies.append({
                    'source_id': t3_supplier['id'],
                    'target_id': t2_supplier['id'],
                    'dependency_weight': weight
                })
        
        # Tier-2 → Tier-1 connections
        for _, t1_supplier in tier1.iterrows():
            # Each Tier-1 gets 2-5 Tier-2 suppliers
            n_suppliers = np.random.randint(2, 6)
            t2_sources = tier2.sample(n=min(n_suppliers, len(tier2)))
            
            for _, t2_supplier in t2_sources.iterrows():
                weight = np.random.randint(40, 100)
                
                dependencies.append({
                    'source_id': t2_supplier['id'],
                    'target_id': t1_supplier['id'],
                    'dependency_weight': weight
                })
        
        df = pd.DataFrame(dependencies)
        print(f"[OK] Generated {len(df)} dependency edges")
        return df
    
    def generate_product_bom(self, 
                            suppliers_df: pd.DataFrame,
                            n_products: int = 10) -> pd.DataFrame:
        """
        Generate product Bill of Materials.
        
        Maps which suppliers feed which products.
        
        Args:
            suppliers_df: DataFrame with supplier data
            n_products: Number of products to create
            
        Returns:
            DataFrame with product BOM data
        """
        print(f"Generating {n_products} product BOMs...")
        
        tier1 = suppliers_df[suppliers_df['tier'] == 1]
        
        products = []
        
        product_names = [
            "SmartSensor Pro X1",
            "Industrial Controller Z400",
            "DataLogger Elite",
            "Precision Monitor DX",
            "AutomationHub 5000",
            "FlexDisplay Module",
            "PowerCore System",
            "ConnectNode Gateway",
            "EdgeProcessor Unit",
            "SecureComm Platform"
        ]
        
        for i in range(n_products):
            product_id = f"P{i+1:03d}"
            product_name = product_names[i] if i < len(product_names) else f"Product {i+1}"
            
            # Annual revenue: between 2M and 15M euros
            annual_revenue = round(np.random.uniform(2.0, 15.0), 2)
            
            # Each product uses 3-8 Tier-1 suppliers
            n_suppliers = np.random.randint(3, 9)
            product_suppliers = tier1.sample(n=min(n_suppliers, len(tier1)))
            
            # Create comma-separated list of supplier IDs
            supplier_ids = ','.join(product_suppliers['id'].tolist())
            
            products.append({
                'product_id': product_id,
                'product_name': product_name,
                'annual_revenue_eur_m': annual_revenue,
                'component_supplier_ids': supplier_ids
            })
        
        df = pd.DataFrame(products)
        print(f"[OK] Generated {len(df)} products")
        return df
    
    def save_all(self, output_dir: Path) -> None:
        """
        Generate all data and save to CSV files.
        
        Args:
            output_dir: Directory to save CSV files (e.g., data/raw)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print("SUPPLIERSHIELD DATA GENERATION")
        print(f"{'='*60}\n")
        
        # Load country risk data
        country_risk_path = output_dir / 'country_risk.csv'
        self.load_country_risk(country_risk_path)
        
        # Generate suppliers
        suppliers_df = self.generate_suppliers(
            n_tier1=40,
            n_tier2=40,
            n_tier3=40
        )
        suppliers_path = output_dir / 'suppliers.csv'
        suppliers_df.to_csv(suppliers_path, index=False)
        print(f"[OK] Saved to {suppliers_path}\n")
        
        # Generate dependencies
        dependencies_df = self.generate_dependencies(suppliers_df)
        dependencies_path = output_dir / 'dependencies.csv'
        dependencies_df.to_csv(dependencies_path, index=False)
        print(f"[OK] Saved to {dependencies_path}\n")
        
        # Generate product BOMs
        product_bom_df = self.generate_product_bom(suppliers_df, n_products=10)
        bom_path = output_dir / 'product_bom.csv'
        product_bom_df.to_csv(bom_path, index=False)
        print(f"[OK] Saved to {bom_path}\n")
        
        print(f"{'='*60}")
        print("DATA GENERATION COMPLETE!")
        print(f"{'='*60}\n")
        
        # Print summary
        print("Summary:")
        print(f"  • {len(suppliers_df)} suppliers across 3 tiers")
        print(f"  • {len(dependencies_df)} supplier dependencies")
        print(f"  • {len(product_bom_df)} products")
        print(f"  • {len(self.country_risk)} countries")