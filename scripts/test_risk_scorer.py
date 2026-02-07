"""
Test script for the risk scoring engine.

This script calculates risk scores for all suppliers and displays the results.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer


def main():
    """Test the risk scorer."""
    
    print("="*60)
    print("RISK SCORING ENGINE TEST")
    print("="*60 + "\n")
    
    # Step 1: Load data
    print("Step 1: Loading data...")
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    
    # Step 2: Build network
    print("\nStep 2: Building network...")
    builder = SupplierNetworkBuilder()
    builder.load_data(suppliers, dependencies, country_risk)
    graph = builder.build_graph()
    
    # Step 3: Calculate risk scores
    print("\nStep 3: Calculating risk scores...")
    scorer = RiskScorer(graph)
    risk_scores = scorer.calculate_all_risks()
    
    # Step 4: Add scores to graph
    scorer.add_scores_to_graph()
    
    # Step 5: Analyze results
    print("\n" + "="*60)
    print("RISK SCORE ANALYSIS")
    print("="*60 + "\n")
    
    # Show top 10 highest risk suppliers
    print("Top 10 Highest Risk Suppliers:")
    print("-"*60)
    
    # Sort by composite risk (highest first)
    sorted_suppliers = sorted(
        risk_scores.items(),
        key=lambda x: x[1]['composite'],
        reverse=True
    )
    
    for i, (supplier_id, scores) in enumerate(sorted_suppliers[:10], 1):
        node = graph.nodes[supplier_id]
        print(f"\n{i}. {supplier_id} - {node['name']}")
        print(f"   Composite Risk: {scores['composite']:.1f}/100 [{scores['category']}]")
        print(f"   Tier: {node['tier']} | Component: {node['component']}")
        print(f"   Country: {node['country']} | Contract: €{node['contract_value_eur_m']}M")
        print(f"   Risk Breakdown:")
        print(f"     • Geopolitical: {scores['geopolitical']:.1f}")
        print(f"     • Natural Disaster: {scores['natural_disaster']:.1f}")
        print(f"     • Financial: {scores['financial']:.1f}")
        print(f"     • Logistics: {scores['logistics']:.1f}")
        print(f"     • Concentration: {scores['concentration']:.1f}")
    
    # Show top 5 lowest risk suppliers
    print("\n" + "="*60)
    print("\nTop 5 Lowest Risk Suppliers:")
    print("-"*60)
    
    for i, (supplier_id, scores) in enumerate(sorted_suppliers[-5:], 1):
        node = graph.nodes[supplier_id]
        print(f"\n{i}. {supplier_id} - {node['name']}")
        print(f"   Composite Risk: {scores['composite']:.1f}/100 [{scores['category']}]")
        print(f"   Country: {node['country']} | Tier: {node['tier']}")
    
    # Analyze high-risk suppliers
    print("\n" + "="*60)
    high_risk = scorer.get_high_risk_suppliers(threshold=55.0)
    critical_risk = scorer.get_high_risk_suppliers(threshold=75.0)
    
    print(f"\nHigh-Risk Suppliers (score ≥ 55): {len(high_risk)}")
    print(f"Critical-Risk Suppliers (score ≥ 75): {len(critical_risk)}")
    
    # Show critical suppliers by tier
    if critical_risk:
        print("\nCritical Suppliers by Tier:")
        tier_breakdown = {1: [], 2: [], 3: []}
        for sid in critical_risk.keys():
            tier = graph.nodes[sid]['tier']
            tier_breakdown[tier].append(sid)
        
        for tier in [1, 2, 3]:
            count = len(tier_breakdown[tier])
            print(f"  • Tier-{tier}: {count} critical suppliers")
            if count > 0 and count <= 3:
                print(f"    {tier_breakdown[tier]}")
    
    # Show example of risk verification
    print("\n" + "="*60)
    print("\nDetailed Risk Verification for One Supplier:")
    print("-"*60)
    
    # Pick the highest risk supplier
    highest_risk_id = sorted_suppliers[0][0]
    node = graph.nodes[highest_risk_id]
    scores = risk_scores[highest_risk_id]
    
    print(f"\nSupplier: {highest_risk_id} - {node['name']}")
    print(f"Country: {node['country']}")
    print(f"\nRaw Country Data:")
    print(f"  • Political Stability Index: {node.get('political_stability', 'N/A')}")
    print(f"  • Natural Disaster Freq: {node.get('natural_disaster_freq', 'N/A')}")
    print(f"  • Logistics Performance: {node.get('logistics_performance', 'N/A')}")
    print(f"\nSupplier-Specific Data:")
    print(f"  • Financial Health: {node.get('financial_health', 'N/A')}/100")
    print(f"  • Incoming Suppliers: {len(list(graph.predecessors(highest_risk_id)))}")
    print(f"\nCalculated Risk Scores:")
    print(f"  • Geopolitical: {scores['geopolitical']:.1f} (weight: 30%)")
    print(f"  • Natural Disaster: {scores['natural_disaster']:.1f} (weight: 20%)")
    print(f"  • Financial: {scores['financial']:.1f} (weight: 20%)")
    print(f"  • Logistics: {scores['logistics']:.1f} (weight: 15%)")
    print(f"  • Concentration: {scores['concentration']:.1f} (weight: 15%)")
    print(f"\n  → COMPOSITE: {scores['composite']:.1f}/100 [{scores['category']}]")
    
    # Manual verification
    manual_composite = (
        scores['geopolitical'] * 0.30 +
        scores['natural_disaster'] * 0.20 +
        scores['financial'] * 0.20 +
        scores['logistics'] * 0.15 +
        scores['concentration'] * 0.15
    )
    print(f"\nManual Calculation Verification: {manual_composite:.2f}")
    print(f"Matches? {abs(manual_composite - scores['composite']) < 0.01}")
    
    print("\n" + "="*60)
    print("✅ Risk scoring test complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()