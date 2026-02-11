"""
Test script for the network builder.

This script builds the supplier network graph and displays information about it.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.network.validator import NetworkValidator


def main():
    """Test the network builder."""
    
    print("="*60)
    print("SUPPLIER NETWORK BUILDER TEST")
    print("="*60 + "\n")
    
    # Step 1: Load data
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    
    # Step 2: Build network
    builder = SupplierNetworkBuilder()
    builder.load_data(suppliers, dependencies, country_risk)
    graph = builder.build_graph()
    
    # Step 3: Test some queries
    print("\n" + "="*60)
    print("TESTING NETWORK QUERIES")
    print("="*60 + "\n")
    
    # Get Tier-1 suppliers
    tier1_suppliers = builder.get_tier_suppliers(1)
    print(f"Tier-1 suppliers: {len(tier1_suppliers)}")
    print(f"First 5: {tier1_suppliers[:5]}\n")
    
    # Pick a random Tier-1 supplier and show its dependencies
    test_supplier = tier1_suppliers[0]
    print(f"Analyzing supplier: {test_supplier}")
    
    # Get attributes
    attrs = builder.get_node_attributes(test_supplier)
    print(f"  Name: {attrs['name']}")
    print(f"  Component: {attrs['component']}")
    print(f"  Country: {attrs['country']}")
    print(f"  Contract Value: €{attrs['contract_value_eur_m']}M")
    print(f"  Financial Health: {attrs['financial_health']}/100")
    print(f"  Has Backup: {attrs['has_backup']}\n")
    
    # Get dependencies
    deps = builder.get_supplier_dependencies(test_supplier)
    print(f"  Upstream suppliers (feeds into {test_supplier}): {len(deps['upstream'])}")
    if deps['upstream']:
        print(f"    Example: {deps['upstream'][:3]}")
    
    print(f"  Downstream suppliers ({test_supplier} feeds into): {len(deps['downstream'])}")
    if deps['downstream']:
        print(f"    Example: {deps['downstream'][:3]}")
    
    # Test Tier-2 supplier
    print("\n" + "-"*60 + "\n")
    tier2_suppliers = builder.get_tier_suppliers(2)
    test_supplier_2 = tier2_suppliers[0]
    
    print(f"Analyzing supplier: {test_supplier_2}")
    attrs2 = builder.get_node_attributes(test_supplier_2)
    print(f"  Name: {attrs2['name']}")
    print(f"  Component: {attrs2['component']}")
    print(f"  Tier: {attrs2['tier']}")
    
    deps2 = builder.get_supplier_dependencies(test_supplier_2)
    print(f"  Upstream (Tier-3 suppliers): {len(deps2['upstream'])}")
    print(f"  Downstream (Tier-1 suppliers): {len(deps2['downstream'])}")
    
    # Test Tier-3 supplier
    print("\n" + "-"*60 + "\n")
    tier3_suppliers = builder.get_tier_suppliers(3)
    test_supplier_3 = tier3_suppliers[0]
    
    print(f"Analyzing supplier: {test_supplier_3}")
    attrs3 = builder.get_node_attributes(test_supplier_3)
    print(f"  Name: {attrs3['name']}")
    print(f"  Component: {attrs3['component']}")
    print(f"  Tier: {attrs3['tier']}")
    
    deps3 = builder.get_supplier_dependencies(test_supplier_3)
    print(f"  Upstream (should be 0, Tier-3 has no suppliers): {len(deps3['upstream'])}")
    print(f"  Downstream (Tier-2 suppliers this feeds): {len(deps3['downstream'])}")
    
    # Step 4: Validate the network
    print("\n" + "="*60)
    print("RUNNING NETWORK VALIDATION")
    print("="*60)
    
    net_validator = NetworkValidator(graph)
    is_valid = net_validator.validate_all()
    
    # Get network metrics
    if is_valid:
        print("\nNetwork Metrics:")
        metrics = net_validator.get_network_metrics()
        print(f"  • Nodes: {metrics['num_nodes']}")
        print(f"  • Edges: {metrics['num_edges']}")
        print(f"  • Average out-degree: {metrics['avg_out_degree']:.2f}")
        print(f"  • Average in-degree: {metrics['avg_in_degree']:.2f}")
        print(f"  • Max out-degree: {metrics['max_out_degree']}")
        print(f"  • Max in-degree: {metrics['max_in_degree']}")
        print(f"  • Network density: {metrics['density']:.4f}")
        print(f"  • Tier distribution: {metrics['tier_distribution']}")
    
    print("\n" + "="*60)
    print("[OK] Network builder test complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()