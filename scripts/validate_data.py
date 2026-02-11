"""
Script to validate generated data.

Run this after generate_data.py to verify data quality.
"""

import sys
from pathlib import Path

# Add the src directory to Python's path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator


def main():
    """Validate all data files."""
    
    # Define data directory
    data_dir = project_root / 'data' / 'raw'
    
    # Create validator
    validator = DataValidator(data_dir)
    
    # Load all data
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    
    # Run validation checks
    is_valid = validator.validate_all()
    
    # Print summary statistics
    if is_valid:
        print("\nSUMMARY STATISTICS:")
        print("="*60)
        stats = validator.get_summary_stats()
        
        print(f"Suppliers:")
        print(f"  • Total: {stats['total_suppliers']}")
        print(f"  • Tier-1: {stats['tier_1_count']}")
        print(f"  • Tier-2: {stats['tier_2_count']}")
        print(f"  • Tier-3: {stats['tier_3_count']}")
        
        print(f"\nDependencies: {stats['total_dependencies']} edges")
        print(f"Products: {stats['total_products']}")
        print(f"Countries: {stats['total_countries']}")
        
        print(f"\nTop 3 Countries by Supplier Count:")
        for country, count in stats['top_3_countries'].items():
            print(f"  • {country}: {count} suppliers")
        
        print("\n" + "="*60)
        print("[OK] Data validation complete!")
    else:
        print("\n[WARNING] Please fix validation errors before proceeding.")
    
    return is_valid


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)