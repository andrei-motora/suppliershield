"""
Risk propagation engine for SupplierShield.

This module cascades risk scores through the supplier network tiers,
revealing hidden vulnerabilities when safe suppliers depend on risky ones.
"""

import networkx as nx
from typing import Dict, List
import numpy as np


class RiskPropagator:
    """
    Propagates risk scores through the supplier network.
    
    Risk flows bottom-up:
    - Tier-3 → Tier-2 → Tier-1
    
    A supplier's propagated risk considers both its own composite risk
    and the risk inherited from suppliers it depends on.
    """
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialize the risk propagator.
        
        Args:
            graph: NetworkX graph with risk scores already calculated
        """
        self.graph = graph
        self.propagated_risks = {}  # {supplier_id: propagated_risk}
    
    def propagate_all_risks(self) -> Dict[str, float]:
        """
        Propagate risk through all tiers of the network.
        
        Returns:
            Dictionary mapping supplier_id to propagated risk score
        """
        print("\n" + "="*60)
        print("PROPAGATING RISK THROUGH NETWORK")
        print("="*60 + "\n")
        
        # Step 1: Get suppliers by tier
        tier_1 = [n for n in self.graph.nodes() if self.graph.nodes[n]['tier'] == 1]
        tier_2 = [n for n in self.graph.nodes() if self.graph.nodes[n]['tier'] == 2]
        tier_3 = [n for n in self.graph.nodes() if self.graph.nodes[n]['tier'] == 3]
        
        print(f"Processing {len(tier_3)} Tier-3 suppliers...")
        # Step 2: Tier-3 has no dependencies (they're at the bottom)
        for node_id in tier_3:
            composite_risk = self.graph.nodes[node_id]['risk_composite']
            self.propagated_risks[node_id] = composite_risk
        
        print(f"✓ Tier-3 propagated risks set (same as composite)")
        
        # Step 3: Propagate to Tier-2
        print(f"\nProcessing {len(tier_2)} Tier-2 suppliers...")
        for node_id in tier_2:
            self.propagated_risks[node_id] = self._propagate_node_risk(node_id)
        
        print(f"✓ Tier-2 risks propagated")
        
        # Step 4: Propagate to Tier-1
        print(f"\nProcessing {len(tier_1)} Tier-1 suppliers...")
        for node_id in tier_1:
            self.propagated_risks[node_id] = self._propagate_node_risk(node_id)
        
        print(f"✓ Tier-1 risks propagated")
        
        # Add propagated risks to graph nodes
        self._add_to_graph()
        
        # Print summary
        self._print_propagation_summary()
        
        return self.propagated_risks
    
    def _propagate_node_risk(self, node_id: str) -> float:
        """
        Calculate propagated risk for a single node.
        
        Args:
            node_id: Supplier ID
            
        Returns:
            Propagated risk score (0-100)
        """
        # Get this node's own composite risk
        own_risk = self.graph.nodes[node_id]['risk_composite']
        
        # Get all suppliers that feed INTO this node (predecessors)
        upstream_suppliers = list(self.graph.predecessors(node_id))
        
        if not upstream_suppliers:
            # No dependencies = propagated risk is just own risk
            return own_risk
        
        # Calculate average propagated risk of upstream suppliers
        upstream_risks = [
            self.propagated_risks[supplier_id]
            for supplier_id in upstream_suppliers
        ]
        avg_upstream_risk = np.mean(upstream_risks)
        
        # Calculate propagated risk: 60% own risk + 40% inherited risk
        # But never decrease risk (use max)
        propagated = max(
            own_risk,
            own_risk * 0.6 + avg_upstream_risk * 0.4
        )
        
        return float(propagated)
    
    def _add_to_graph(self) -> None:
        """Add propagated risk scores to graph nodes."""
        print("\nAdding propagated risks to graph nodes...")
        
        for node_id, propagated_risk in self.propagated_risks.items():
            self.graph.nodes[node_id]['risk_propagated'] = round(propagated_risk, 2)
        
        print("✓ Propagated risks added to graph")
    
    def _print_propagation_summary(self) -> None:
        """Print summary statistics about risk propagation."""
        print("\nRisk Propagation Summary:")
        
        # Calculate how much risk increased
        increases = []
        for node_id in self.graph.nodes():
            composite = self.graph.nodes[node_id]['risk_composite']
            propagated = self.propagated_risks[node_id]
            increase = propagated - composite
            increases.append(increase)
        
        avg_increase = np.mean(increases)
        max_increase = np.max(increases)
        
        # Count how many suppliers had risk increase
        increased_count = sum(1 for i in increases if i > 0.1)
        
        print(f"  • Average risk increase: {avg_increase:.2f} points")
        print(f"  • Maximum risk increase: {max_increase:.2f} points")
        print(f"  • Suppliers with increased risk: {increased_count}/{len(increases)}")
        
        # Show propagated risk distribution
        propagated_values = list(self.propagated_risks.values())
        print(f"\nPropagated Risk Statistics:")
        print(f"  • Average: {np.mean(propagated_values):.2f}")
        print(f"  • Min: {np.min(propagated_values):.2f}")
        print(f"  • Max: {np.max(propagated_values):.2f}")
        print(f"  • Median: {np.median(propagated_values):.2f}")
    
    def get_biggest_risk_increases(self, n: int = 10) -> List[tuple]:
        """
        Get suppliers with the biggest risk increases from propagation.
        
        Args:
            n: Number of suppliers to return
            
        Returns:
            List of (supplier_id, composite_risk, propagated_risk, increase) tuples
        """
        increases = []
        
        for node_id in self.graph.nodes():
            composite = self.graph.nodes[node_id]['risk_composite']
            propagated = self.propagated_risks[node_id]
            increase = propagated - composite
            
            increases.append((
                node_id,
                composite,
                propagated,
                increase
            ))
        
        # Sort by increase (largest first)
        increases.sort(key=lambda x: x[3], reverse=True)
        
        return increases[:n]
    
    def analyze_hidden_vulnerabilities(self) -> Dict:
        """
        Find suppliers that look safe but have hidden vulnerabilities.
        
        Returns:
            Dictionary with analysis results
        """
        hidden_vulns = []
        
        # Find suppliers with low composite risk but high propagated risk
        for node_id in self.graph.nodes():
            composite = self.graph.nodes[node_id]['risk_composite']
            propagated = self.propagated_risks[node_id]
            
            # Hidden vulnerability: composite is LOW/MEDIUM but propagated is HIGH/CRITICAL
            if composite < 55 and propagated >= 55:
                increase = propagated - composite
                hidden_vulns.append({
                    'supplier_id': node_id,
                    'name': self.graph.nodes[node_id]['name'],
                    'tier': self.graph.nodes[node_id]['tier'],
                    'composite': composite,
                    'propagated': propagated,
                    'increase': increase
                })
        
        # Sort by increase
        hidden_vulns.sort(key=lambda x: x['increase'], reverse=True)
        
        return {
            'count': len(hidden_vulns),
            'suppliers': hidden_vulns
        }
    
    def trace_risk_path(self, node_id: str) -> List[Dict]:
        """
        Trace the risk propagation path for a specific supplier.
        
        Shows the chain of dependencies that contribute to propagated risk.
        
        Args:
            node_id: Supplier ID to trace
            
        Returns:
            List of dictionaries showing the risk path
        """
        path = []
        
        # Start with this node
        current_tier = self.graph.nodes[node_id]['tier']
        
        path.append({
            'supplier_id': node_id,
            'name': self.graph.nodes[node_id]['name'],
            'tier': current_tier,
            'composite_risk': self.graph.nodes[node_id]['risk_composite'],
            'propagated_risk': self.propagated_risks[node_id]
        })
        
        # Get upstream suppliers (who feeds this node)
        upstream = list(self.graph.predecessors(node_id))
        
        if upstream:
            for supplier_id in upstream:
                path.append({
                    'supplier_id': supplier_id,
                    'name': self.graph.nodes[supplier_id]['name'],
                    'tier': self.graph.nodes[supplier_id]['tier'],
                    'composite_risk': self.graph.nodes[supplier_id]['risk_composite'],
                    'propagated_risk': self.propagated_risks[supplier_id]
                })
        
        return path