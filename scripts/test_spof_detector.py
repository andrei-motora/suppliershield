"""
Test script for the SPOF (Single Point of Failure) detector.

This script identifies critical suppliers whose failure would
break the supply chain.
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
from src.risk.spof_detector import SPOFDetector


def main():
    """Test the SPOF detector."""
    
    print("="*60)
    print("SPOF (SINGLE POINT OF FAILURE) DETECTOR TEST")
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
    
    # Step 4: Detect SPOFs
    print("\nStep 4: Detecting Single Points of Failure...")
    spof_detector = SPOFDetector(graph)
    spofs = spof_detector.detect_all_spofs()
    
    # Step 5: Analyze results
    print("\n" + "="*60)
    print("SPOF ANALYSIS RESULTS")
    print("="*60 + "\n")
    
    if not spofs:
        print("✅ No Single Points of Failure detected!")
        print("All critical suppliers have backup options.")
    else:
        # Get detailed SPOF information
        spof_details = spof_detector.get_spof_details()
        
        print(f"🚨 Found {len(spofs)} Single Points of Failure\n")
        print("-"*60)
        
        for i, spof in enumerate(spof_details, 1):
            print(f"\n{i}. {spof['supplier_id']} - {spof['name']}")
            print(f"   Tier: {spof['tier']} | Component: {spof['component']}")
            print(f"   Country: {spof['country']}")
            print(f"   Contract Value: €{spof['contract_value_eur_m']}M")
            print(f"   Composite Risk: {spof['composite_risk']:.1f}")
            print(f"   Propagated Risk: {spof['propagated_risk']:.1f}")
            print(f"   Direct Impact: {spof['direct_impact']} suppliers depend on this")
            print(f"   Total Impact: {spof['total_impact']} suppliers in downstream chain")
            
            # Get detailed impact analysis
            impact = spof_detector.analyze_spof_impact(spof['supplier_id'])
            print(f"\n   If this SPOF fails:")
            print(f"     • {impact['tier_1_affected']} Tier-1 suppliers affected")
            print(f"     • {impact['tier_2_affected']} Tier-2 suppliers affected")
            print(f"     • {impact['tier_3_affected']} Tier-3 suppliers affected")
            print(f"     • €{impact['total_contract_value_at_risk']}M total contract value at risk")
        
        # Identify critical SPOFs (high risk + SPOF)
        print("\n" + "="*60)
        print("\nCRITICAL SPOFs (High Risk + No Backup)")
        print("="*60)
        
        critical_spofs = spof_detector.get_critical_spofs(risk_threshold=60.0)
        
        if critical_spofs:
            print(f"\n🔴 Found {len(critical_spofs)} CRITICAL SPOFs (risk ≥ 60)\n")
            print("-"*60)
            
            for spof_id in critical_spofs:
                node = graph.nodes[spof_id]
                print(f"\n{spof_id} - {node['name']}")
                print(f"  Tier: {node['tier']} | Component: {node['component']}")
                print(f"  Country: {node['country']}")
                print(f"  Propagated Risk: {node['risk_propagated']:.1f}")
                print(f"  ⚠️  URGENT: This is both high-risk AND a single point of failure!")
        else:
            print("\n✅ No critical SPOFs (all SPOFs have acceptable risk levels)")
        
        # Summary recommendations
        print("\n" + "="*60)
        print("\nRECOMMENDATIONS")
        print("="*60 + "\n")
        
        # Prioritize by risk level
        high_priority = [s for s in spof_details if s['propagated_risk'] >= 60]
        medium_priority = [s for s in spof_details if 40 <= s['propagated_risk'] < 60]
        low_priority = [s for s in spof_details if s['propagated_risk'] < 40]
        
        if high_priority:
            print("🔴 HIGH PRIORITY (0-30 days):")
            for spof in high_priority:
                print(f"  • Qualify backup supplier for {spof['supplier_id']} ({spof['component']})")
        
        if medium_priority:
            print("\n🟡 MEDIUM PRIORITY (30-90 days):")
            for spof in medium_priority:
                print(f"  • Establish dual-sourcing for {spof['supplier_id']} ({spof['component']})")
        
        if low_priority:
            print("\n🟢 LOW PRIORITY (90+ days):")
            for spof in low_priority:
                print(f"  • Monitor and consider backup for {spof['supplier_id']} ({spof['component']})")
        
        # Statistics
        print("\n" + "="*60)
        print("\nSPOF STATISTICS")
        print("="*60 + "\n")
        
        # Count suppliers without backups
        total_suppliers = graph.number_of_nodes()
        no_backup_count = sum(1 for n in graph.nodes() if not graph.nodes[n]['has_backup'])
        
        print(f"Total Suppliers: {total_suppliers}")
        print(f"Suppliers without backup: {no_backup_count} ({no_backup_count/total_suppliers*100:.1f}%)")
        print(f"SPOFs detected: {len(spofs)} ({len(spofs)/total_suppliers*100:.1f}%)")
        print(f"\nSPOF Detection Rate: {len(spofs)/no_backup_count*100:.1f}% of no-backup suppliers are SPOFs")
        
        # Most impactful SPOF
        if spof_details:
            most_impactful = spof_details[0]
            print(f"\nMost Impactful SPOF:")
            print(f"  {most_impactful['supplier_id']} - {most_impactful['name']}")
            print(f"  Affects {most_impactful['total_impact']} downstream suppliers")
            print(f"  €{most_impactful['contract_value_eur_m']}M contract value")
    
    print("\n" + "="*60)
    print("✅ SPOF detection test complete!")
    print("="*60 + "\n")
    
    # Export summary
    print("Summary for Management:")
    print("-"*60)
    print(f"• Total Suppliers Analyzed: {graph.number_of_nodes()}")
    print(f"• Single Points of Failure: {len(spofs)}")
    
    critical_count = len(spof_detector.get_critical_spofs(60.0))
    print(f"• Critical SPOFs (high risk + no backup): {critical_count}")
    
    if spofs:
        total_impact = sum(s['total_impact'] for s in spof_details)
        print(f"• Total Suppliers in SPOF Dependency Chains: {total_impact}")
        
        total_value = sum(s['contract_value_eur_m'] for s in spof_details)
        print(f"• Total Contract Value of SPOFs: €{total_value:.2f}M")
    
    print("\n")


if __name__ == '__main__':
    main()