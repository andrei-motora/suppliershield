"""
Comprehensive test for Phase 3 - All features together.

This script demonstrates:
1. Monte Carlo Disruption Simulation
2. Sensitivity Analysis (Criticality Ranking)
3. BOM Impact Tracing
4. Recommendation Engine

Shows the complete analytical workflow for supply chain risk management.
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
from src.simulation.monte_carlo import MonteCarloSimulator
from src.simulation.sensitivity import SensitivityAnalyzer
from src.impact.bom_tracer import BOMImpactTracer
from src.recommendations.engine import RecommendationEngine


def main():
    """Run comprehensive Phase 3 analysis."""
    
    print("="*60)
    print("SUPPLIERSHIELD - PHASE 3 COMPREHENSIVE ANALYSIS")
    print("="*60 + "\n")
    
    print("This analysis demonstrates:")
    print("  1. Monte Carlo Disruption Simulation")
    print("  2. Sensitivity Analysis (Criticality Ranking)")
    print("  3. BOM Impact Tracing")
    print("  4. Recommendation Engine")
    print()
    
    # ================================================================
    # SETUP: Load data and build network
    # ================================================================
    
    print("\n" + "="*60)
    print("PHASE 1: DATA LOADING & NETWORK CONSTRUCTION")
    print("="*60 + "\n")
    
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    
    builder = SupplierNetworkBuilder()
    builder.load_data(suppliers, dependencies, country_risk)
    graph = builder.build_graph()
    
    # ================================================================
    # PHASE 2: Risk Analysis
    # ================================================================
    
    print("\n" + "="*60)
    print("PHASE 2: RISK SCORING & PROPAGATION")
    print("="*60 + "\n")
    
    scorer = RiskScorer(graph)
    risk_scores = scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    propagator = RiskPropagator(graph)
    propagated_risks = propagator.propagate_all_risks()
    
    spof_detector = SPOFDetector(graph)
    spofs = spof_detector.detect_all_spofs()
    
    print(f"\n✓ Phase 2 complete: {len(spofs)} SPOFs detected")
    
    # ================================================================
    # PHASE 3 FEATURE 1: Monte Carlo Simulation
    # ================================================================
    
    print("\n" + "="*60)
    print("PHASE 3 FEATURE 1: MONTE CARLO SIMULATION")
    print("="*60 + "\n")
    
    simulator = MonteCarloSimulator(
        graph=graph,
        product_bom_df=product_bom,
        seed=42
    )
    
    # Run simulation on most critical SPOF
    print("Running simulation on S016 (most impactful SPOF)...\n")
    
    mc_result = simulator.run_simulation(
        target_supplier='S016',
        duration_days=30,
        iterations=3000,
        scenario_type='single_node'
    )
    
    print(f"\n✓ Monte Carlo complete: €{mc_result['mean']:.2f}M mean impact")
    
    # ================================================================
    # PHASE 3 FEATURE 2: Sensitivity Analysis
    # ================================================================
    
    print("\n" + "="*60)
    print("PHASE 3 FEATURE 2: SENSITIVITY ANALYSIS")
    print("="*60 + "\n")
    
    analyzer = SensitivityAnalyzer(
        graph=graph,
        product_bom_df=product_bom
    )
    
    top_critical = analyzer.get_top_critical(n=10)
    
    print("Top 10 Most Critical Suppliers:")
    print("-" * 60)
    for idx, row in top_critical.iterrows():
        print(f"{idx}. {row['supplier_id']} - {row['name']}")
        print(f"   Criticality: {row['criticality_score']:.2f} | Risk: {row['propagated_risk']:.1f} | Exposure: €{row['total_revenue_exposure']:.2f}M")
    
    pareto = analyzer.get_pareto_analysis()
    print(f"\n✓ Sensitivity complete: Top {pareto['pareto_50_suppliers']} suppliers = 50% of risk")
    
    # ================================================================
    # PHASE 3 FEATURE 3: BOM Impact Tracing
    # ================================================================
    
    print("\n" + "="*60)
    print("PHASE 3 FEATURE 3: BOM IMPACT TRACING")
    print("="*60 + "\n")
    
    tracer = BOMImpactTracer(
        graph=graph,
        product_bom_df=product_bom
    )
    
    # Trace impact of most critical supplier
    most_critical_id = top_critical.iloc[0]['supplier_id']
    
    print(f"Tracing impact of most critical supplier: {most_critical_id}\n")
    
    bom_impact = tracer.trace_supplier_impact(most_critical_id)
    
    print(f"\n✓ BOM trace complete: {bom_impact['product_count']} products affected, €{bom_impact['total_revenue_at_risk']:.2f}M at risk")
    
    # Also trace a product's dependencies
    print("\n" + "-"*60)
    product_deps = tracer.trace_product_dependencies('P001')
    
    # ================================================================
    # PHASE 3 FEATURE 4: Recommendation Engine
    # ================================================================
    
    print("\n" + "="*60)
    print("PHASE 3 FEATURE 4: RECOMMENDATION ENGINE")
    print("="*60 + "\n")
    
    rec_engine = RecommendationEngine(
        graph=graph,
        product_bom_df=product_bom
    )
    
    recommendations = rec_engine.generate_all_recommendations()
    regional_recs = rec_engine.generate_regional_recommendations()
    
    # Print recommendations
    rec_engine.print_recommendations(recommendations)
    
    # Executive summary
    summary = rec_engine.generate_executive_summary(recommendations)
    
    print("\n" + "="*60)
    print("EXECUTIVE SUMMARY")
    print("="*60 + "\n")
    
    print(f"Total Recommendations: {summary['total_recommendations']}")
    print(f"  • CRITICAL: {summary['critical_count']}")
    print(f"  • HIGH: {summary['high_count']}")
    print(f"  • MEDIUM: {summary['medium_count']}")
    print(f"  • WATCH: {summary['watch_count']}")
    print()
    print(f"Contract Value at Risk:")
    print(f"  • CRITICAL suppliers: €{summary['critical_contract_value']:.2f}M")
    print(f"  • HIGH priority suppliers: €{summary['high_contract_value']:.2f}M")
    print()
    print(f"Scope:")
    print(f"  • {summary['unique_suppliers']} suppliers require action")
    print(f"  • {summary['unique_countries']} countries affected")
    
    # ================================================================
    # INTEGRATED INSIGHTS
    # ================================================================
    
    print("\n" + "="*60)
    print("INTEGRATED INSIGHTS - ALL FEATURES COMBINED")
    print("="*60 + "\n")
    
    print("1. RISK IDENTIFICATION (Phase 2):")
    print(f"   • 120 suppliers analyzed across 3 tiers")
    print(f"   • {len(spofs)} single points of failure detected")
    print(f"   • Risk propagation revealed hidden vulnerabilities")
    
    print("\n2. IMPACT QUANTIFICATION (Monte Carlo):")
    print(f"   • S016 disruption: €{mc_result['mean']:.2f}M expected loss")
    print(f"   • Worst case scenario: €{mc_result['max']:.2f}M")
    print(f"   • 95th percentile: €{mc_result['p95']:.2f}M")
    
    print("\n3. PRIORITIZATION (Sensitivity Analysis):")
    print(f"   • Top {pareto['pareto_50_suppliers']} suppliers = 50% of total risk")
    print(f"   • Top {pareto['pareto_80_suppliers']} suppliers = 80% of total risk")
    print(f"   • Tier-3 has highest average criticality")
    
    print("\n4. DEPENDENCY MAPPING (BOM Tracing):")
    print(f"   • Most critical supplier affects {bom_impact['product_count']} products")
    print(f"   • Total revenue at risk: €{bom_impact['total_revenue_at_risk']:.2f}M")
    print(f"   • Cascade impact: {bom_impact['cascade_impact']} downstream suppliers")
    
    print("\n5. ACTION PLAN (Recommendations):")
    print(f"   • {summary['critical_count']} CRITICAL actions (0-30 days)")
    print(f"   • {summary['high_count']} HIGH priority actions (30-60 days)")
    print(f"   • {summary['medium_count']} MEDIUM priority actions (60-90 days)")
    print(f"   • {summary['watch_count']} ongoing monitoring items")
    
    # ================================================================
    # DECISION-MAKING WORKFLOW
    # ================================================================
    
    print("\n" + "="*60)
    print("DECISION-MAKING WORKFLOW FOR MANAGEMENT")
    print("="*60 + "\n")
    
    print("Step 1: IDENTIFY HIGH-RISK SUPPLIERS")
    print("  → Use risk propagation to find hidden vulnerabilities")
    print("  → Result: Focus on suppliers with propagated risk ≥ 60")
    
    print("\nStep 2: QUANTIFY FINANCIAL IMPACT")
    print("  → Run Monte Carlo simulation on critical suppliers")
    print("  → Result: Budget €14M contingency for top risks")
    
    print("\nStep 3: PRIORITIZE BY CRITICALITY")
    print("  → Use sensitivity analysis: Risk × Exposure")
    print(f"  → Result: Focus on top {pareto['pareto_50_suppliers']} suppliers first")
    
    print("\nStep 4: MAP PRODUCT DEPENDENCIES")
    print("  → Trace BOM to understand product impact")
    print("  → Result: Know which products are affected by each supplier")
    
    print("\nStep 5: EXECUTE RECOMMENDATIONS")
    print(f"  → Start with {summary['critical_count']} CRITICAL actions")
    print("  → Qualify backup suppliers for high-risk components")
    print("  → Diversify away from concentrated regions")
    
    print("\n" + "="*60)
    print("✅ PHASE 3 COMPREHENSIVE ANALYSIS COMPLETE!")
    print("="*60 + "\n")
    
    print("Portfolio Value:")
    print("  • Demonstrates advanced analytics: Monte Carlo, graph theory, optimization")
    print("  • Shows business impact: Revenue quantification, prioritization, ROI")
    print("  • Provides actionable insights: Not just analysis, but recommendations")
    print("  • Interview-ready: Can explain every algorithm and business decision")
    print()


if __name__ == '__main__':
    main()