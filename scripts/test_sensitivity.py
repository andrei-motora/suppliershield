"""
Test script for sensitivity analysis (criticality ranking).

This script ranks suppliers by criticality - which single supplier
failure would cause the most damage.
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
from src.simulation.sensitivity import SensitivityAnalyzer


def main():
    """Test the sensitivity analyzer."""
    
    print("="*60)
    print("SENSITIVITY ANALYSIS TEST")
    print("="*60 + "\n")
    
    # Step 1: Load data and build network
    print("Step 1: Loading data and building network...")
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    
    builder = SupplierNetworkBuilder()
    builder.load_data(suppliers, dependencies, country_risk)
    graph = builder.build_graph()
    
    # Step 2: Calculate and propagate risks
    print("\nStep 2: Calculating risk scores...")
    scorer = RiskScorer(graph)
    risk_scores = scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    print("\nStep 3: Propagating risks...")
    propagator = RiskPropagator(graph)
    propagated_risks = propagator.propagate_all_risks()
    
    # Step 4: Initialize sensitivity analyzer
    print("\nStep 4: Initializing sensitivity analyzer...")
    analyzer = SensitivityAnalyzer(
        graph=graph,
        product_bom_df=product_bom
    )
    
    print("[OK] Analyzer initialized\n")
    
    # ================================================================
    # TOP 20 CRITICAL SUPPLIERS
    # ================================================================
    
    analyzer.print_top_critical(n=20)
    
    # ================================================================
    # TIER ANALYSIS
    # ================================================================
    
    print("\n" + "="*60)
    print("CRITICALITY BY TIER")
    print("="*60 + "\n")
    
    tier_stats = analyzer.analyze_by_tier()
    print(tier_stats.to_string(index=False))
    
    print("\nInsights:")
    print("  • Which tier has highest average criticality?")
    print("  • Which tier has the most critical single supplier?")
    
    # ================================================================
    # COUNTRY ANALYSIS
    # ================================================================
    
    print("\n" + "="*60)
    print("CRITICALITY BY COUNTRY (TOP 10)")
    print("="*60 + "\n")
    
    country_stats = analyzer.analyze_by_country(top_n=10)
    print(country_stats.to_string())
    
    print("\nInsights:")
    print("  • Which countries concentrate the most risk?")
    print("  • Where should we focus diversification efforts?")
    
    # ================================================================
    # CRITICAL CLUSTERS
    # ================================================================
    
    print("\n" + "="*60)
    print("CRITICAL SUPPLIER CLUSTERS")
    print("="*60 + "\n")
    
    print("Analyzing suppliers with criticality >= 10.0...\n")
    
    clusters = analyzer.identify_critical_clusters(criticality_threshold=10.0)
    
    print(f"Total Critical Suppliers: {clusters['total_critical']}\n")
    
    print("By Country:")
    print(clusters['by_country'].to_string())
    
    print("\n\nBy Tier:")
    print(clusters['by_tier'].to_string())
    
    # ================================================================
    # RISK VS EXPOSURE MATRIX
    # ================================================================
    
    print("\n" + "="*60)
    print("RISK VS EXPOSURE MATRIX")
    print("="*60 + "\n")
    
    risk_exposure = analyzer.compare_risk_vs_exposure()
    
    # Count by category
    category_counts = risk_exposure['category'].value_counts()
    
    print("Supplier Distribution:")
    for category, count in category_counts.items():
        print(f"  • {category}: {count} suppliers")
    
    print("\nTop 10 in Each Category:\n")
    
    for category in category_counts.index:
        cat_df = risk_exposure[risk_exposure['category'] == category].head(10)
        if len(cat_df) > 0:
            print(f"\n{category}:")
            print("-" * 60)
            for _, row in cat_df.iterrows():
                print(f"  {row['supplier_id']} - {row['name']}")
                print(f"    Risk: {row['risk']:.1f} | Exposure: €{row['exposure']:.2f}M | Criticality: {row['criticality']:.2f}")
    
    # ================================================================
    # PARETO ANALYSIS
    # ================================================================
    
    print("\n" + "="*60)
    print("PARETO ANALYSIS (80/20 RULE)")
    print("="*60 + "\n")
    
    pareto = analyzer.get_pareto_analysis()
    
    print(f"Total Suppliers: {pareto['total_suppliers']}")
    print(f"Total Criticality: {pareto['total_criticality']:.2f}\n")
    
    print("Pareto Findings:")
    print(f"  • 50% of criticality comes from: {pareto['pareto_50_suppliers']} suppliers ({pareto['pareto_50_percent']:.1f}%)")
    print(f"  • 80% of criticality comes from: {pareto['pareto_80_suppliers']} suppliers ({pareto['pareto_80_percent']:.1f}%)")
    print(f"  • Top 10 suppliers account for: {pareto['top_10_percent']:.1f}% of total criticality")
    
    print("\n\nTop 10 Most Critical:")
    print("-" * 60)
    top_10 = analyzer.get_top_critical(n=10)
    for idx, row in top_10.iterrows():
        print(f"{idx}. {row['supplier_id']} - {row['name']}")
        print(f"   Criticality: {row['criticality_score']:.2f} | Risk: {row['propagated_risk']:.1f} | Exposure: €{row['total_revenue_exposure']:.2f}M")
    
    # ================================================================
    # BUSINESS RECOMMENDATIONS
    # ================================================================
    
    print("\n" + "="*60)
    print("BUSINESS RECOMMENDATIONS")
    print("="*60 + "\n")
    
    print("Priority Actions:")
    print()
    
    # Top 5 critical
    top_5 = analyzer.get_top_critical(n=5)
    
    print("[!!] URGENT (0-30 days):")
    for idx, row in top_5.iterrows():
        print(f"  {idx}. {row['supplier_id']} - Criticality: {row['criticality_score']:.2f}")
        print(f"     Action: Qualify backup supplier for {row['component']}")
        print(f"     Reason: {row['risk_category']} risk + €{row['total_revenue_exposure']:.2f}M exposure")
    
    # Clusters
    print("\n[!] STRATEGIC (30-90 days):")
    print(f"  • Diversify sourcing away from countries with highest criticality")
    print(f"  • Focus on: {', '.join(country_stats.head(3).index.tolist())}")
    
    # Tier focus
    highest_tier = tier_stats.loc[tier_stats['Avg Criticality'].idxmax()]
    print(f"\n[~] LONG-TERM (90+ days):")
    print(f"  • Strengthen Tier-{int(highest_tier['Tier'])} supplier relationships")
    print(f"  • This tier has highest average criticality: {highest_tier['Avg Criticality']:.2f}")
    
    print("\n" + "="*60)
    print("INTERPRETATION FOR MANAGEMENT")
    print("="*60 + "\n")
    
    print("What criticality score means:")
    print("  • Criticality = Risk x Revenue Exposure")
    print("  • High criticality = High risk AND/OR high revenue impact")
    print("  • Focus mitigation on highest criticality suppliers first")
    print()
    
    print("Key Insights:")
    print(f"  • Top {pareto['pareto_50_suppliers']} suppliers ({pareto['pareto_50_percent']:.1f}%) drive 50% of total risk")
    print(f"  • Just {pareto['pareto_80_suppliers']} suppliers ({pareto['pareto_80_percent']:.1f}%) account for 80% of criticality")
    print(f"  • {clusters['total_critical']} suppliers exceed criticality threshold of 10.0")
    
    print("\n" + "="*60)
    print("[OK] Sensitivity analysis test complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()