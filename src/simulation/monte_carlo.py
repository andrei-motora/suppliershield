"""
Monte Carlo disruption simulator for SupplierShield.

This module runs probabilistic simulations to estimate revenue-at-risk
when suppliers fail. Runs thousands of scenarios to capture uncertainty.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
import random
import time


class MonteCarloSimulator:
    """
    Monte Carlo disruption simulator.
    
    Runs thousands of random scenarios to estimate the distribution of
    revenue impact when suppliers fail. Answers: "What's the expected
    revenue loss? What's the worst case?"
    """
    
    def __init__(self, 
                 graph: nx.DiGraph,
                 product_bom_df: pd.DataFrame,
                 seed: int = 42):
        """
        Initialize the simulator.
        
        Args:
            graph: NetworkX graph with risk scores and propagation
            product_bom_df: Product BOM data (product → suppliers → revenue)
            seed: Random seed for reproducibility
        """
        self.graph = graph
        self.product_bom_df = product_bom_df
        self.seed = seed
        
        # Set random seeds for reproducibility
        np.random.seed(seed)
        random.seed(seed)
        
        # Build product-to-supplier mapping
        self._build_product_supplier_map()
    
    def _build_product_supplier_map(self) -> None:
        """Build a mapping of which suppliers feed which products."""
        self.product_supplier_map = {}
        
        for _, product in self.product_bom_df.iterrows():
            product_id = product['product_id']
            supplier_ids = product['component_supplier_ids'].split(',')
            
            self.product_supplier_map[product_id] = {
                'name': product['product_name'],
                'revenue': product['annual_revenue_eur_m'],
                'suppliers': supplier_ids
            }
    
    def run_simulation(self,
                      target_supplier: str,
                      duration_days: int,
                      iterations: int = 5000,
                      scenario_type: str = 'single_node') -> Dict:
        """
        Run Monte Carlo simulation for a disruption scenario.
        
        Args:
            target_supplier: Supplier ID that fails (e.g., "S024")
            duration_days: How long the disruption lasts (7-90 days)
            iterations: Number of Monte Carlo iterations (1000-10000)
            scenario_type: 'single_node', 'regional', or 'correlated'
            
        Returns:
            Dictionary with simulation results and statistics
        """
        print("\n" + "="*60)
        print("MONTE CARLO DISRUPTION SIMULATION")
        print("="*60 + "\n")
        
        print(f"Scenario: {scenario_type}")
        print(f"Target: {target_supplier}")
        print(f"Duration: {duration_days} days")
        print(f"Iterations: {iterations:,}")
        print()
        
        # Get affected suppliers based on scenario type
        affected_suppliers = self._get_affected_suppliers(
            target_supplier,
            scenario_type
        )
        
        print(f"Potentially affected suppliers: {len(affected_suppliers)}")
        print(f"Running {iterations:,} simulations...")

        # Run all iterations
        start_time = time.time()
        results = []
        for i in range(iterations):
            impact = self._run_single_iteration(
                affected_suppliers,
                duration_days
            )
            results.append(impact)
            
            # Progress indicator
            if (i + 1) % 1000 == 0:
                print(f"  Completed {i + 1:,} / {iterations:,} iterations...")
        
        elapsed = time.time() - start_time
        print(f"[OK] Simulation complete\n")

        # Calculate statistics
        stats = self._calculate_statistics(results)

        # Find affected products
        affected_products = [
            pid for pid, pdata in self.product_supplier_map.items()
            if set(pdata['suppliers']) & affected_suppliers
        ]

        # Add metadata
        stats['target_supplier'] = target_supplier
        stats['duration_days'] = duration_days
        stats['iterations'] = iterations
        stats['scenario_type'] = scenario_type
        stats['affected_suppliers_count'] = len(affected_suppliers)
        stats['affected_products'] = affected_products
        stats['runtime'] = elapsed
        stats['all_results'] = results
        
        # Print summary
        self._print_summary(stats)
        
        return stats
    
    def _get_affected_suppliers(self,
                                target_supplier: str,
                                scenario_type: str) -> Set[str]:
        """
        Get list of suppliers affected by the disruption.
        
        Args:
            target_supplier: Primary supplier that fails
            scenario_type: Type of scenario
            
        Returns:
            Set of supplier IDs that could be affected
        """
        if scenario_type == 'single_node':
            # Just the target + its downstream dependents
            affected = {target_supplier}
            try:
                descendants = nx.descendants(self.graph, target_supplier)
                affected.update(descendants)
            except Exception:
                pass
            return affected
        
        elif scenario_type == 'regional':
            # All suppliers in the same region as target
            target_region = self.graph.nodes[target_supplier]['region']
            affected = {
                node for node in self.graph.nodes()
                if self.graph.nodes[node]['region'] == target_region
            }
            return affected
        
        elif scenario_type == 'correlated':
            # All suppliers that share dependencies with target
            affected = {target_supplier}
            
            # Get upstream suppliers of target
            upstream = set(self.graph.predecessors(target_supplier))
            
            # Find all suppliers that depend on same upstream
            for node in self.graph.nodes():
                node_upstream = set(self.graph.predecessors(node))
                if upstream & node_upstream:  # Intersection
                    affected.add(node)
            
            return affected
        
        else:
            return {target_supplier}
    
    def _run_single_iteration(self,
                             affected_suppliers: Set[str],
                             duration_days: int) -> float:
        """
        Run a single Monte Carlo iteration.
        
        Args:
            affected_suppliers: Suppliers that could fail
            duration_days: Disruption duration
            
        Returns:
            Total revenue impact for this iteration (in €M)
        """
        total_impact = 0.0
        failed_suppliers = set()
        
        # For each affected supplier, determine if it fails
        for supplier_id in affected_suppliers:
            if supplier_id not in self.graph.nodes():
                continue
            
            # Get propagated risk
            propagated_risk = self.graph.nodes[supplier_id].get(
                'risk_propagated',
                self.graph.nodes[supplier_id]['risk_composite']
            )
            
            # Calculate failure probability
            # Higher risk + longer duration = higher probability
            base_probability = propagated_risk / 100.0
            duration_factor = min(duration_days / 30.0, 1.5)  # Cap at 1.5x
            failure_probability = min(base_probability * duration_factor, 0.95)
            
            # Random draw: does this supplier fail?
            if np.random.random() < failure_probability:
                failed_suppliers.add(supplier_id)
        
        # Calculate revenue impact from failed suppliers
        if failed_suppliers:
            total_impact = self._calculate_revenue_impact(failed_suppliers)
        
        return total_impact
    
    def _calculate_revenue_impact(self, failed_suppliers: Set[str]) -> float:
        """
        Calculate revenue impact from a set of failed suppliers.
        
        Args:
            failed_suppliers: Set of supplier IDs that failed
            
        Returns:
            Total revenue impact in €M
        """
        total_impact = 0.0
        affected_products = set()
        
        # Find all products affected by these failures
        for product_id, product_data in self.product_supplier_map.items():
            product_suppliers = set(product_data['suppliers'])
            
            # Does this product depend on any failed supplier?
            if failed_suppliers & product_suppliers:
                affected_products.add(product_id)
                
                # Calculate impact fraction (random between 0.1 and 0.5)
                # Not all revenue is lost - some orders might be delayed, not cancelled
                impact_fraction = np.random.uniform(0.1, 0.5)
                
                # Add to total impact
                product_revenue = product_data['revenue']
                total_impact += product_revenue * impact_fraction
        
        return total_impact
    
    def _calculate_statistics(self, results: List[float]) -> Dict:
        """
        Calculate statistics from simulation results.
        
        Args:
            results: List of revenue impacts from all iterations
            
        Returns:
            Dictionary with statistical measures
        """
        results_array = np.array(results)
        
        return {
            'mean': float(np.mean(results_array)),
            'median': float(np.median(results_array)),
            'std': float(np.std(results_array)),
            'min': float(np.min(results_array)),
            'max': float(np.max(results_array)),
            'p25': float(np.percentile(results_array, 25)),
            'p75': float(np.percentile(results_array, 75)),
            'p90': float(np.percentile(results_array, 90)),
            'p95': float(np.percentile(results_array, 95)),
            'p99': float(np.percentile(results_array, 99))
        }
    
    def _print_summary(self, stats: Dict) -> None:
        """Print simulation results summary."""
        print("Simulation Results:")
        print(f"  • Mean impact: €{stats['mean']:.2f}M")
        print(f"  • Median impact (P50): €{stats['median']:.2f}M")
        print(f"  • 95th percentile (P95): €{stats['p95']:.2f}M")
        print(f"  • 99th percentile (P99): €{stats['p99']:.2f}M")
        print(f"  • Worst case: €{stats['max']:.2f}M")
        print(f"  • Best case: €{stats['min']:.2f}M")
        print(f"  • Standard deviation: €{stats['std']:.2f}M")
    
    def get_histogram_data(self, results: List[float], bins: int = 30) -> Dict:
        """
        Get histogram data for visualization.
        
        Args:
            results: Simulation results
            bins: Number of histogram bins
            
        Returns:
            Dictionary with histogram data
        """
        counts, bin_edges = np.histogram(results, bins=bins)
        
        return {
            'counts': counts.tolist(),
            'bin_edges': bin_edges.tolist(),
            'bin_centers': [(bin_edges[i] + bin_edges[i+1])/2 
                           for i in range(len(bin_edges)-1)]
        }
    
    def compare_scenarios(self,
                         scenarios: List[Dict],
                         iterations: int = 5000) -> pd.DataFrame:
        """
        Compare multiple disruption scenarios side by side.
        
        Args:
            scenarios: List of scenario configs, each with:
                      {'name': str, 'target': str, 'duration': int, 'type': str}
            iterations: Number of iterations per scenario
            
        Returns:
            DataFrame comparing all scenarios
        """
        results = []
        
        for scenario in scenarios:
            print(f"\nRunning scenario: {scenario['name']}")
            stats = self.run_simulation(
                target_supplier=scenario['target'],
                duration_days=scenario['duration'],
                iterations=iterations,
                scenario_type=scenario.get('type', 'single_node')
            )
            
            results.append({
                'Scenario': scenario['name'],
                'Target': scenario['target'],
                'Duration (days)': scenario['duration'],
                'Mean Impact (€M)': stats['mean'],
                'P95 Impact (€M)': stats['p95'],
                'Max Impact (€M)': stats['max'],
                'Affected Suppliers': stats['affected_suppliers_count']
            })
        
        return pd.DataFrame(results)