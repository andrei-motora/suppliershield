"""
Single Point of Failure (SPOF) detection for SupplierShield.

This module identifies critical suppliers whose removal would break
the supply chain or create severe disruptions.
"""

import networkx as nx
from typing import List, Dict, Set
import copy


class SPOFDetector:
    """
    Detects Single Points of Failure in the supplier network.
    
    A supplier is a SPOF if:
    1. It has no backup supplier (has_backup = False)
    2. AND one of:
       - Its removal disconnects the network
       - It has high propagated risk (>60) with no alternative
       - It's the only supplier for a critical component
    """
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialize the SPOF detector.
        
        Args:
            graph: NetworkX graph with risk scores and propagation
        """
        self.graph = graph
        self.spofs = []  # List of SPOF supplier IDs
    
    def detect_all_spofs(self) -> List[str]:
        """
        Detect all Single Points of Failure in the network.
        
        Returns:
            List of supplier IDs that are SPOFs
        """
        print("\n" + "="*60)
        print("DETECTING SINGLE POINTS OF FAILURE (SPOFs)")
        print("="*60 + "\n")
        
        print("Analyzing suppliers for SPOF conditions...")
        
        spof_details = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            
            # Check if supplier has a backup
            has_backup = node_data.get('has_backup', False)
            
            if not has_backup:
                # No backup - check if it's a SPOF
                spof_reason = self._check_spof_conditions(node_id)
                
                if spof_reason:
                    self.spofs.append(node_id)
                    spof_details.append({
                        'supplier_id': node_id,
                        'name': node_data['name'],
                        'tier': node_data['tier'],
                        'component': node_data['component'],
                        'propagated_risk': node_data.get('risk_propagated', node_data['risk_composite']),
                        'reason': spof_reason
                    })
        
        print(f"[OK] Analysis complete")
        
        # Add SPOF flag to graph nodes
        self._add_spof_flags_to_graph()
        
        # Print summary
        self._print_spof_summary(spof_details)
        
        return self.spofs
    
    def _check_spof_conditions(self, node_id: str) -> str:
        """
        Check if a supplier meets SPOF conditions.
        
        Args:
            node_id: Supplier ID to check
            
        Returns:
            Reason string if SPOF, empty string if not
        """
        node_data = self.graph.nodes[node_id]
        propagated_risk = node_data.get('risk_propagated', node_data['risk_composite'])
        
        # Condition 1: High risk with no backup
        if propagated_risk > 60:
            return f"High risk ({propagated_risk:.1f}) with no backup"
        
        # Condition 2: Critical network position
        # Check if this supplier is the ONLY supplier for downstream nodes
        downstream = list(self.graph.successors(node_id))
        
        if downstream:
            # Check if any downstream supplier depends ONLY on this one
            for target_id in downstream:
                upstream_of_target = list(self.graph.predecessors(target_id))
                
                if len(upstream_of_target) == 1:
                    # This is the ONLY supplier for the target
                    target_tier = self.graph.nodes[target_id]['tier']
                    return f"Only supplier for {target_id} (Tier-{target_tier})"
        
        # Condition 3: Removal would disconnect network
        if self._would_disconnect_network(node_id):
            return "Removal would disconnect critical path"
        
        return ""  # Not a SPOF
    
    def _would_disconnect_network(self, node_id: str) -> bool:
        """
        Check if removing this node would disconnect the network.
        
        Args:
            node_id: Supplier ID to test
            
        Returns:
            True if removal disconnects network, False otherwise
        """
        # Create a copy of the graph without this node
        test_graph = self.graph.copy()
        test_graph.remove_node(node_id)
        
        # Check if any Tier-1 nodes became unreachable from Tier-3
        tier_1_nodes = [n for n in test_graph.nodes() if test_graph.nodes[n]['tier'] == 1]
        tier_3_nodes = [n for n in test_graph.nodes() if test_graph.nodes[n]['tier'] == 3]
        
        if not tier_1_nodes or not tier_3_nodes:
            return False
        
        # Check if there's still a path from any Tier-3 to any Tier-1
        for t3_node in tier_3_nodes:
            for t1_node in tier_1_nodes:
                if nx.has_path(test_graph, t3_node, t1_node):
                    return False  # Still connected
        
        # No path found - network is disconnected
        return True
    
    def _add_spof_flags_to_graph(self) -> None:
        """Add SPOF flags to graph nodes."""
        print("\nAdding SPOF flags to graph nodes...")
        
        for node_id in self.graph.nodes():
            is_spof = node_id in self.spofs
            self.graph.nodes[node_id]['is_spof'] = is_spof
        
        print("[OK] SPOF flags added to graph")
    
    def _print_spof_summary(self, spof_details: List[Dict]) -> None:
        """Print summary of detected SPOFs."""
        print(f"\nSPOF Detection Summary:")
        print(f"  • Total SPOFs detected: {len(spof_details)}")
        
        if spof_details:
            # Count by tier
            tier_counts = {}
            for spof in spof_details:
                tier = spof['tier']
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            print(f"\n  SPOFs by Tier:")
            for tier in sorted(tier_counts.keys()):
                print(f"    • Tier-{tier}: {tier_counts[tier]} SPOFs")
            
            # Count by reason
            reason_counts = {}
            for spof in spof_details:
                reason_type = spof['reason'].split('(')[0].strip()
                reason_counts[reason_type] = reason_counts.get(reason_type, 0) + 1
            
            print(f"\n  SPOFs by Reason:")
            for reason, count in reason_counts.items():
                print(f"    • {reason}: {count}")
    
    def get_spof_details(self) -> List[Dict]:
        """
        Get detailed information about all SPOFs.
        
        Returns:
            List of dictionaries with SPOF details
        """
        spof_info = []
        
        for node_id in self.spofs:
            node_data = self.graph.nodes[node_id]
            
            # Get downstream impact (how many suppliers depend on this)
            downstream = list(self.graph.successors(node_id))
            
            # Get all descendants (recursive downstream)
            try:
                descendants = nx.descendants(self.graph, node_id)
            except:
                descendants = set()
            
            spof_info.append({
                'supplier_id': node_id,
                'name': node_data['name'],
                'tier': node_data['tier'],
                'component': node_data['component'],
                'country': node_data['country'],
                'contract_value_eur_m': node_data['contract_value_eur_m'],
                'composite_risk': node_data['risk_composite'],
                'propagated_risk': node_data.get('risk_propagated', node_data['risk_composite']),
                'direct_impact': len(downstream),
                'total_impact': len(descendants),
                'has_backup': node_data['has_backup']
            })
        
        # Sort by total impact (highest first)
        spof_info.sort(key=lambda x: x['total_impact'], reverse=True)
        
        return spof_info
    
    def get_critical_spofs(self, risk_threshold: float = 60.0) -> List[str]:
        """
        Get SPOFs that also have high risk.
        
        Args:
            risk_threshold: Minimum propagated risk to be critical
            
        Returns:
            List of critical SPOF supplier IDs
        """
        critical = []
        
        for node_id in self.spofs:
            propagated_risk = self.graph.nodes[node_id].get(
                'risk_propagated',
                self.graph.nodes[node_id]['risk_composite']
            )
            
            if propagated_risk >= risk_threshold:
                critical.append(node_id)
        
        return critical
    
    def analyze_spof_impact(self, spof_id: str) -> Dict:
        """
        Analyze the impact if a specific SPOF fails.
        
        Args:
            spof_id: SPOF supplier ID
            
        Returns:
            Dictionary with impact analysis
        """
        if spof_id not in self.spofs:
            return {'error': 'Not a SPOF'}
        
        # Get all downstream suppliers
        try:
            descendants = nx.descendants(self.graph, spof_id)
        except:
            descendants = set()
        
        # Count by tier
        tier_impact = {1: 0, 2: 0, 3: 0}
        for desc_id in descendants:
            tier = self.graph.nodes[desc_id]['tier']
            tier_impact[tier] += 1
        
        # Calculate total contract value at risk
        total_value = self.graph.nodes[spof_id]['contract_value_eur_m']
        for desc_id in descendants:
            total_value += self.graph.nodes[desc_id]['contract_value_eur_m']
        
        return {
            'spof_id': spof_id,
            'name': self.graph.nodes[spof_id]['name'],
            'direct_downstream': len(list(self.graph.successors(spof_id))),
            'total_affected': len(descendants),
            'tier_1_affected': tier_impact[1],
            'tier_2_affected': tier_impact[2],
            'tier_3_affected': tier_impact[3],
            'total_contract_value_at_risk': round(total_value, 2)
        }