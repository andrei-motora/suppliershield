"""
Test script for the risk propagation engine.

This script demonstrates how risk cascades through supplier tiers,
revealing hidden vulnerabilities.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer
from src.risk.propagation import RiskPropagator


def main():
    """Test the risk propagation engine."""
    
    print("="*60)
    print("RISK PROPAGATION ENGINE TEST")
    print("="*60 + "\n")
    
    # Step 1: Load data and build network
    print("Step 1: Loading data and building network...")
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    
    builder = SupplierNetworkBuilder()
    builder.load_data(suppliers, dependencies, country_risk)
    graph = builder.build_graph()
    
    # Step 2: Calculate base risk scores
    print("\nStep 2: Calculating base risk scores...")
    scorer = RiskScorer(graph)
    risk_scores = scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    # Step 3: Propagate risks
    print("\nStep 3: Propagating risks through network...")
    propagator = RiskPropagator(graph)
    propagated_risks = propagator.propagate_all_risks()
    
    # Step 4: Analyze results
    print("\n" + "="*60)
    print("RISK PROPAGATION ANALYSIS")
    print("="*60 + "\n")
    
    # Show top 10 biggest risk increases
    print("Top 10 Suppliers with Biggest Risk Increases:")
    print("-"*60)
    
    biggest_increases = propagator.get_biggest_risk_increases(n=10)
    
    for i, (supplier_id, composite, propagated, increase) in enumerate(biggest_increases, 1):
        node = graph.nodes[supplier_id]
        print(f"\n{i}. {supplier_id} - {node['name']}")
        print(f"   Tier: {node['tier']} | Country: {node['country']}")
        print(f"   Composite Risk: {composite:.1f}")
        print(f"   Propagated Risk: {propagated:.1f}")
        print(f"   ⬆️  Increase: +{increase:.1f} points")
        
        # Show what it depends on
        upstream = list(graph.predecessors(supplier_id))
        if upstream:
            print(f"   Depends on {len(upstream)} suppliers:")
            for up_id in upstream[:3]:  # Show first 3
                up_risk = propagated_risks[up_id]
                print(f"     • {up_id} (risk: {up_risk:.1f})")
            if len(upstream) > 3:
                print(f"     ... and {len(upstream)-3} more")
    
    # Analyze hidden vulnerabilities
    print("\n" + "="*60)
    print("\nHIDDEN VULNERABILITIES ANALYSIS")
    print("="*60)
    
    hidden_vulns = propagator.analyze_hidden_vulnerabilities()
    
    print(f"\nSuppliers that LOOK safe but have HIDDEN risk:")
    print(f"(Composite < 55 but Propagated ≥ 55)")
    print(f"\nFound: {hidden_vulns['count']} hidden vulnerabilities\n")
    
    if hidden_vulns['count'] > 0:
        print("-"*60)
        for i, vuln in enumerate(hidden_vulns['suppliers'][:5], 1):
            print(f"\n{i}. {vuln['supplier_id']} - {vuln['name']}")
            print(f"   Tier: {vuln['tier']}")
            print(f"   Composite Risk: {vuln['composite']:.1f} [looks safe]")
            print(f"   Propagated Risk: {vuln['propagated']:.1f} [actually risky!]")
            print(f"   Hidden Vulnerability: +{vuln['increase']:.1f} points")
    else:
        print("No hidden vulnerabilities found (all suppliers' risks match their dependencies)")
    
    # Trace a specific risk path
    print("\n" + "="*60)
    print("\nRISK PATH TRACING - Example")
    print("="*60)
    
    # Pick a supplier with a big risk increase
    if biggest_increases:
        example_id = biggest_increases[0][0]
        print(f"\nTracing risk path for: {example_id}")
        print("-"*60)
        
        path = propagator.trace_risk_path(example_id)
        
        for step in path:
            print(f"\n{step['supplier_id']} - {step['name']}")
            print(f"  Tier: {step['tier']}")
            print(f"  Composite Risk: {step['composite_risk']:.1f}")
            print(f"  Propagated Risk: {step['propagated_risk']:.1f}")
            if step['propagated_risk'] > step['composite_risk']:
                print(f"  ⚠️  Risk increased by {step['propagated_risk'] - step['composite_risk']:.1f} points")
    
    # Compare composite vs propagated across all tiers
    print("\n" + "="*60)
    print("\nCOMPOSITE vs PROPAGATED RISK BY TIER")
    print("="*60 + "\n")
    
    for tier in [1, 2, 3]:
        tier_nodes = [n for n in graph.nodes() if graph.nodes[n]['tier'] == tier]
        
        composite_avg = sum(graph.nodes[n]['risk_composite'] for n in tier_nodes) / len(tier_nodes)
        propagated_avg = sum(propagated_risks[n] for n in tier_nodes) / len(tier_nodes)
        
        print(f"Tier-{tier} ({len(tier_nodes)} suppliers):")
        print(f"  • Average Composite Risk: {composite_avg:.2f}")
        print(f"  • Average Propagated Risk: {propagated_avg:.2f}")
        print(f"  • Average Increase: {propagated_avg - composite_avg:.2f} points")
        print()
    
    # Show before/after for a few specific suppliers
    print("="*60)
    print("\nBEFORE/AFTER EXAMPLES")
    print("="*60)
    
    # Pick 3 interesting cases
    print("\nCase 1: High composite risk (should stay high)")
    high_risk_suppliers = [n for n in graph.nodes() if graph.nodes[n]['risk_composite'] > 70]
    if high_risk_suppliers:
        example = high_risk_suppliers[0]
        print(f"{example} - {graph.nodes[example]['name']}")
        print(f"  Before (composite): {graph.nodes[example]['risk_composite']:.1f}")
        print(f"  After (propagated): {propagated_risks[example]:.1f}")
    
    print("\nCase 2: Low composite risk (might increase)")
    low_risk_suppliers = [n for n in graph.nodes() if graph.nodes[n]['risk_composite'] < 20]
    if low_risk_suppliers:
        example = low_risk_suppliers[0]
        print(f"{example} - {graph.nodes[example]['name']}")
        print(f"  Before (composite): {graph.nodes[example]['risk_composite']:.1f}")
        print(f"  After (propagated): {propagated_risks[example]:.1f}")
        increase = propagated_risks[example] - graph.nodes[example]['risk_composite']
        if increase > 5:
            print(f"  ⚠️  Significant increase: +{increase:.1f} points")
    
    print("\nCase 3: Medium composite risk")
    med_risk_suppliers = [n for n in graph.nodes() if 40 < graph.nodes[n]['risk_composite'] < 50]
    if med_risk_suppliers:
        example = med_risk_suppliers[0]
        print(f"{example} - {graph.nodes[example]['name']}")
        print(f"  Before (composite): {graph.nodes[example]['risk_composite']:.1f}")
        print(f"  After (propagated): {propagated_risks[example]:.1f}")
    
    print("\n" + "="*60)
    print("✅ Risk propagation test complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()