"""
Data loading and validation for SupplierShield.

This module loads CSV files and validates that they follow the correct schemas.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple


class DataValidator:
    """
    Validates SupplierShield data files.
    
    Checks that CSV files have the correct columns, no missing values,
    and that relationships between files are valid.
    """
    
    def __init__(self, data_dir: Path):
        """
        Initialize validator.
        
        Args:
            data_dir: Directory containing CSV files (e.g., data/raw)
        """
        self.data_dir = Path(data_dir)
        self.suppliers = None
        self.dependencies = None
        self.country_risk = None
        self.product_bom = None
    
    def load_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load all CSV files.
        
        Returns:
            Tuple of (suppliers, dependencies, country_risk, product_bom) DataFrames
        """
        print("Loading data files...")
        
        self.suppliers = pd.read_csv(self.data_dir / 'suppliers.csv')
        print(f"[OK] Loaded {len(self.suppliers)} suppliers")

        self.dependencies = pd.read_csv(self.data_dir / 'dependencies.csv')
        print(f"[OK] Loaded {len(self.dependencies)} dependencies")

        self.country_risk = pd.read_csv(self.data_dir / 'country_risk.csv')
        print(f"[OK] Loaded {len(self.country_risk)} countries")

        self.product_bom = pd.read_csv(self.data_dir / 'product_bom.csv')
        print(f"[OK] Loaded {len(self.product_bom)} products")
        
        return self.suppliers, self.dependencies, self.country_risk, self.product_bom
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all validations pass, False otherwise
        """
        print("\n" + "="*60)
        print("VALIDATION CHECKS")
        print("="*60 + "\n")
        
        all_valid = True
        
        # Check 1: No missing values
        if not self._check_no_nulls():
            all_valid = False
        
        # Check 2: Tier values are valid (1, 2, or 3)
        if not self._check_tier_values():
            all_valid = False
        
        # Check 3: All dependency edges reference valid suppliers
        if not self._check_dependency_edges():
            all_valid = False
        
        # Check 4: All countries in suppliers exist in country_risk
        if not self._check_country_consistency():
            all_valid = False
        
        # Check 5: All product supplier IDs are valid
        if not self._check_product_bom_suppliers():
            all_valid = False
        
        print("\n" + "="*60)
        if all_valid:
            print("[PASS] ALL VALIDATIONS PASSED!")
        else:
            print("[FAIL] SOME VALIDATIONS FAILED")
        print("="*60 + "\n")
        
        return all_valid
    
    def _check_no_nulls(self) -> bool:
        """Check that no data files have missing values."""
        print("Check 1: No missing values...")
        
        has_nulls = False
        
        for name, df in [
            ('suppliers', self.suppliers),
            ('dependencies', self.dependencies),
            ('country_risk', self.country_risk),
            ('product_bom', self.product_bom)
        ]:
            null_count = df.isnull().sum().sum()
            if null_count > 0:
                print(f"  [FAIL] {name}.csv has {null_count} missing values")
                has_nulls = True
            else:
                print(f"  [OK] {name}.csv has no missing values")
        
        return not has_nulls
    
    def _check_tier_values(self) -> bool:
        """Check that all tier values are 1, 2, or 3."""
        print("\nCheck 2: Valid tier values...")
        
        valid_tiers = {1, 2, 3}
        actual_tiers = set(self.suppliers['tier'].unique())
        
        if actual_tiers == valid_tiers:
            print(f"  [OK] All tiers are valid: {sorted(actual_tiers)}")
            return True
        else:
            print(f"  [FAIL] Invalid tiers found: {actual_tiers}")
            return False
    
    def _check_dependency_edges(self) -> bool:
        """Check that all dependency edges reference valid supplier IDs."""
        print("\nCheck 3: Valid dependency edges...")
        
        supplier_ids = set(self.suppliers['id'])
        source_ids = set(self.dependencies['source_id'])
        target_ids = set(self.dependencies['target_id'])
        
        invalid_sources = source_ids - supplier_ids
        invalid_targets = target_ids - supplier_ids
        
        if not invalid_sources and not invalid_targets:
            print(f"  [OK] All {len(self.dependencies)} edges reference valid suppliers")
            return True
        else:
            if invalid_sources:
                print(f"  [FAIL] Invalid source IDs: {invalid_sources}")
            if invalid_targets:
                print(f"  [FAIL] Invalid target IDs: {invalid_targets}")
            return False
    
    def _check_country_consistency(self) -> bool:
        """Check that all countries in suppliers exist in country_risk."""
        print("\nCheck 4: Country consistency...")
        
        risk_countries = set(self.country_risk['country_code'])
        supplier_countries = set(self.suppliers['country_code'])
        
        missing = supplier_countries - risk_countries
        
        if not missing:
            print(f"  [OK] All {len(supplier_countries)} countries have risk data")
            return True
        else:
            print(f"  [FAIL] Missing country risk data for: {missing}")
            return False
    
    def _check_product_bom_suppliers(self) -> bool:
        """Check that all supplier IDs in product BOMs are valid."""
        print("\nCheck 5: Valid product BOM supplier IDs...")
        
        supplier_ids = set(self.suppliers['id'])
        
        all_valid = True
        for _, product in self.product_bom.iterrows():
            # Split comma-separated supplier IDs
            bom_supplier_ids = product['component_supplier_ids'].split(',')
            
            for sid in bom_supplier_ids:
                if sid not in supplier_ids:
                    print(f"  [FAIL] Product {product['product_id']} references invalid supplier: {sid}")
                    all_valid = False

        if all_valid:
            print(f"  [OK] All product BOMs reference valid suppliers")
        
        return all_valid
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics about the data.
        
        Returns:
            Dictionary with summary statistics
        """
        tier_counts = self.suppliers['tier'].value_counts().to_dict()
        country_counts = self.suppliers['country'].value_counts()
        
        return {
            'total_suppliers': len(self.suppliers),
            'tier_1_count': tier_counts.get(1, 0),
            'tier_2_count': tier_counts.get(2, 0),
            'tier_3_count': tier_counts.get(3, 0),
            'total_dependencies': len(self.dependencies),
            'total_products': len(self.product_bom),
            'total_countries': len(self.country_risk),
            'top_3_countries': country_counts.head(3).to_dict()
        }