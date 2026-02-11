"""
Test script for the Monte Carlo disruption simulator.

This script runs probabilistic simulations to estimate revenue-at-risk
when suppliers fail.
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
from src.simulation.monte_carlo import MonteCarloSimulator
import pandas as pd


def main():
    """Test the Monte Carlo simulator."""
    
    print("="*60)
    print("MONTE CARLO DISRUPTION SIMULATOR TEST")
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
    
    # Step 4: Initialize Monte Carlo simulator
    print("\nStep 4: Initializing Monte Carlo simulator...")
    simulator = MonteCarloSimulator(
        graph=graph,
        product_bom_df=product_bom,
        seed=42  # For reproducible results
    )
    
    print("[OK] Simulator initialized\n")
    
    # ================================================================
    # SCENARIO 1: Single high-risk supplier failure
    # ================================================================
    
    print("\n" + "="*60)
    print("SCENARIO 1: High-Risk Supplier Knockout")
    print("="*60 + "\n")
    
    # S024 is one of the highest-risk suppliers (DR Congo, risk ~77)
    print("Testing: S024 - DR Congo supplier (CRITICAL risk)")
    print("Question: If this supplier goes offline for 30 days,")
    print("          what's the revenue impact?\n")
    
    scenario1 = simulator.run_simulation(
        target_supplier='S024',
        duration_days=30,
        iterations=5000,
        scenario_type='single_node'
    )
    
    # ================================================================
    # SCENARIO 2: Regional disruption
    # ================================================================
    
    print("\n" + "="*60)
    print("SCENARIO 2: Regional Disruption")
    print("="*60 + "\n")
    
    # What if entire Asia-Pacific region has issues?
    print("Testing: All Asia-Pacific suppliers disrupted")
    print("Question: What if a regional event (typhoon, earthquake)")
    print("          affects all suppliers in Asia-Pacific?\n")
    
    # Pick an Asia-Pacific supplier as target
    asia_pacific_suppliers = [
        node for node in graph.nodes()
        if graph.nodes[node]['region'] == 'Asia-Pacific'
    ]
    
    if asia_pacific_suppliers:
        scenario2 = simulator.run_simulation(
            target_supplier=asia_pacific_suppliers[0],  # Use first as representative
            duration_days=21,  # 3 weeks
            iterations=3000,
            scenario_type='regional'
        )
    
    # ================================================================
    # SCENARIO 3: Most impactful SPOF
    # ================================================================
    
    print("\n" + "="*60)
    print("SCENARIO 3: SPOF Failure")
    print("="*60 + "\n")
    
    # S016 was identified as most impactful SPOF (affects 20 suppliers)
    print("Testing: S016 - US Plastic Resin (affects 20 suppliers)")
    print("Question: What happens if this critical bottleneck fails?\n")
    
    scenario3 = simulator.run_simulation(
        target_supplier='S016',
        duration_days=45,  # 6 weeks
        iterations=5000,
        scenario_type='single_node'
    )
    
    # ================================================================
    # SCENARIO COMPARISON
    # ================================================================
    
    print("\n" + "="*60)
    print("SCENARIO COMPARISON")
    print("="*60 + "\n")
    
    comparison = pd.DataFrame([
        {
            'Scenario': 'S024 - DR Congo (30 days)',
            'Type': 'Single Node',
            'Mean Impact': f"€{scenario1['mean']:.2f}M",
            'P95 Impact': f"€{scenario1['p95']:.2f}M",
            'Worst Case': f"€{scenario1['max']:.2f}M"
        },
        {
            'Scenario': 'Asia-Pacific Regional (21 days)',
            'Type': 'Regional',
            'Mean Impact': f"€{scenario2['mean']:.2f}M",
            'P95 Impact': f"€{scenario2['p95']:.2f}M",
            'Worst Case': f"€{scenario2['max']:.2f}M"
        },
        {
            'Scenario': 'S016 - US SPOF (45 days)',
            'Type': 'Single Node',
            'Mean Impact': f"€{scenario3['mean']:.2f}M",
            'P95 Impact': f"€{scenario3['p95']:.2f}M",
            'Worst Case': f"€{scenario3['max']:.2f}M"
        }
    ])
    
    print(comparison.to_string(index=False))
    
    # ================================================================
    # BUSINESS INSIGHTS
    # ================================================================
    
    print("\n" + "="*60)
    print("BUSINESS INSIGHTS")
    print("="*60 + "\n")
    
    print("Key Findings:")
    print(f"  1. High-risk supplier (S024) disruption:")
    print(f"     • Expected loss: €{scenario1['mean']:.2f}M")
    print(f"     • Bad scenario (P95): €{scenario1['p95']:.2f}M")
    print(f"     • Worst case: €{scenario1['max']:.2f}M")
    
    print(f"\n  2. Regional disruption (Asia-Pacific):")
    print(f"     • Expected loss: €{scenario2['mean']:.2f}M")
    print(f"     • This is {scenario2['mean']/scenario1['mean']:.1f}x worse than single supplier")
    
    print(f"\n  3. SPOF failure (S016, 45 days):")
    print(f"     • Expected loss: €{scenario3['mean']:.2f}M")
    print(f"     • Despite low risk, large network impact")
    
    print("\n" + "="*60)
    print("INTERPRETATION FOR MANAGEMENT")
    print("="*60 + "\n")
    
    print("What these numbers mean:")
    print("  • MEAN: Expected revenue loss in typical disruption")
    print("  • P95: Revenue loss in a 'bad luck' scenario (1 in 20 chance)")
    print("  • MAX: Worst possible outcome from simulations")
    print()
    print("Decision-making:")
    print(f"  • S024 disruption: Budget €{scenario1['p95']:.2f}M contingency")
    print(f"  • Regional risk: Consider geographic diversification")
    print(f"  • SPOF risk: Qualify backup for S016 immediately")
    
    print("\n" + "="*60)
    print("[OK] Monte Carlo simulation test complete!")
    print("="*60 + "\n")
    
    # Show histogram info
    print("Histogram Data (for visualization):")
    hist_data = simulator.get_histogram_data(scenario1['all_results'], bins=30)
    print(f"  • Number of bins: 30")
    print(f"  • Range: €{min(hist_data['bin_edges']):.2f}M - €{max(hist_data['bin_edges']):.2f}M")
    print(f"  • Most common outcome: ~€{hist_data['bin_centers'][hist_data['counts'].index(max(hist_data['counts']))]:.2f}M")
    print()


if __name__ == '__main__':
    main()