"""
Script to generate synthetic supplier data.

Run this script to create all CSV files needed for SupplierShield.
"""

import sys
from pathlib import Path

# Add the src directory to Python's path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.generator import SupplierDataGenerator


def main():
    """Generate all synthetic data files."""
    
    # Define output directory
    output_dir = project_root / 'data' / 'raw'
    
    # Create generator with seed for reproducibility
    generator = SupplierDataGenerator(seed=42)
    
    # Generate and save all data
    generator.save_all(output_dir)
    
    print("\n✅ All data files generated successfully!")
    print(f"\nFiles are in: {output_dir}")
    print("\nNext step: Build the network graph!")


if __name__ == '__main__':
    main()