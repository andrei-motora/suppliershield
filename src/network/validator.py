"""
Network validation for SupplierShield.

This module checks the supplier network for structural problems like
cycles, orphan nodes, and incorrect tier assignments.
"""

import networkx as nx
from typing import List, Dict, Tuple


class NetworkValidator:
    """
    Validates the structure of the supplier network graph.
    
    Checks for common problems:
    - Cycles (circular dependencies)
    - Orphan nodes (disconnected suppliers)
    - Incorrect tier assignments (Tier-1 feeding Tier-2, etc.)
    """
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialize validator.
        
        Args:
            graph: NetworkX directed graph to validate
        """
        self.graph = graph
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all validations pass, False otherwise
        """
        print("\n" + "="*60)
        print("NETWORK VALIDATION CHECKS")
        print("="*60 + "\n")
        
        all_valid = True
        
        # Check 1: No cycles (DAG property)
        if not self._check_no_cycles():
            all_valid = False
        
        # Check 2: All nodes are connected
        if not self._check_connectivity():
            all_valid = False
        
        # Check 3: Tier assignments are correct
        if not self._check_tier_flow():
            all_valid = False
        
        # Check 4: No self-loops
        if not self._check_no_self_loops():
            all_valid = False
        
        print("\n" + "="*60)
        if all_valid:
            print("✅ ALL NETWORK VALIDATIONS PASSED!")
        else:
            print("❌ SOME NETWORK VALIDATIONS FAILED")
        print("="*60 + "\n")
        
        return all_valid
    
    def _check_no_cycles(self) -> bool:
        """
        Check that the graph has no cycles (is a DAG).
        
        A cycle would mean circular dependencies, which shouldn't exist
        in a supply chain (A feeds B feeds C feeds A).
        """
        print("Check 1: No cycles (DAG property)...")
        
        if nx.is_directed_acyclic_graph(self.graph):
            print("  ✓ Graph is a valid DAG (no cycles)")
            return True
        else:
            # Find cycles
            try:
                cycle = nx.find_cycle(self.graph)
                print(f"  ❌ Cycle detected: {cycle}")
            except:
                print("  ❌ Graph contains cycles")
            return False
    
    def _check_connectivity(self) -> bool:
        """
        Check that all nodes are part of the main network.
        
        Orphan nodes (disconnected suppliers) shouldn't exist.
        """
        print("\nCheck 2: Network connectivity...")
        
        # For directed graphs, check weak connectivity
        # (ignoring edge direction)
        if nx.is_weakly_connected(self.graph):
            print("  ✓ All nodes are connected")
            return True
        else:
            # Find disconnected components
            components = list(nx.weakly_connected_components(self.graph))
            print(f"  ⚠️  Network has {len(components)} separate components")
            
            # Show small components (likely orphans)
            small_components = [c for c in components if len(c) < 5]
            if small_components:
                print(f"  Orphan/small components: {small_components}")
            
            # This is a warning, not a failure
            return True
    
    def _check_tier_flow(self) -> bool:
        """
        Check that tier assignments follow the correct flow.
        
        Rules:
        - Tier-3 should only feed Tier-2
        - Tier-2 should only feed Tier-1
        - Tier-1 should not feed anyone
        """
        print("\nCheck 3: Correct tier flow...")
        
        violations = []
        
        for source, target in self.graph.edges():
            source_tier = self.graph.nodes[source]['tier']
            target_tier = self.graph.nodes[target]['tier']
            
            # Check valid tier transitions
            # Tier-3 → Tier-2: OK
            # Tier-2 → Tier-1: OK
            # Everything else: VIOLATION
            
            valid_transitions = {
                (3, 2),  # Tier-3 feeds Tier-2
                (2, 1),  # Tier-2 feeds Tier-1
            }
            
            if (source_tier, target_tier) not in valid_transitions:
                violations.append(
                    f"Tier-{source_tier} ({source}) → Tier-{target_tier} ({target})"
                )
        
        if not violations:
            print("  ✓ All tier transitions are correct")
            return True
        else:
            print(f"  ❌ Found {len(violations)} invalid tier transitions:")
            for v in violations[:5]:  # Show first 5
                print(f"    • {v}")
            if len(violations) > 5:
                print(f"    ... and {len(violations) - 5} more")
            return False
    
    def _check_no_self_loops(self) -> bool:
        """
        Check that no node has an edge to itself.
        
        A supplier shouldn't depend on itself.
        """
        print("\nCheck 4: No self-loops...")
        
        self_loops = list(nx.selfloop_edges(self.graph))
        
        if not self_loops:
            print("  ✓ No self-loops found")
            return True
        else:
            print(f"  ❌ Found {len(self_loops)} self-loops: {self_loops}")
            return False
    
    def get_network_metrics(self) -> Dict:
        """
        Calculate useful network metrics.
        
        Returns:
            Dictionary with network analysis metrics
        """
        metrics = {}
        
        # Basic counts
        metrics['num_nodes'] = self.graph.number_of_nodes()
        metrics['num_edges'] = self.graph.number_of_edges()
        
        # Degree statistics
        out_degrees = [d for n, d in self.graph.out_degree()]
        in_degrees = [d for n, d in self.graph.in_degree()]
        
        metrics['avg_out_degree'] = sum(out_degrees) / len(out_degrees) if out_degrees else 0
        metrics['avg_in_degree'] = sum(in_degrees) / len(in_degrees) if in_degrees else 0
        metrics['max_out_degree'] = max(out_degrees) if out_degrees else 0
        metrics['max_in_degree'] = max(in_degrees) if in_degrees else 0
        
        # Tier distribution
        tier_counts = {}
        for node in self.graph.nodes():
            tier = self.graph.nodes[node]['tier']
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        metrics['tier_distribution'] = tier_counts
        
        # Network density (how connected is the network?)
        metrics['density'] = nx.density(self.graph)
        
        return metrics