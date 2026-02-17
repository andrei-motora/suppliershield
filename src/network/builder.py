"""
Network graph builder for SupplierShield.

This module converts supplier CSV data into a NetworkX directed graph.
Each supplier is a node, each dependency is an edge.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Set


class SupplierNetworkBuilder:
    """
    Builds a directed graph representation of the supplier network.
    
    The graph structure:
    - Nodes = Suppliers (with all their attributes as node properties)
    - Edges = Dependencies (Tier-3 → Tier-2 → Tier-1)
    - Edge weights = Dependency percentages
    """
    
    def __init__(self):
        """Initialize the network builder."""
        self.graph = nx.DiGraph()  # DiGraph = Directed Graph (arrows have direction)
        self.suppliers_df = None
        self.dependencies_df = None
        self.country_risk_df = None
    
    def load_data(self,
                  suppliers_df: pd.DataFrame,
                  dependencies_df: pd.DataFrame,
                  country_risk_df: pd.DataFrame) -> None:
        """
        Load the data needed to build the network.
        
        Args:
            suppliers_df: Supplier master data
            dependencies_df: Supplier-to-supplier dependencies
            country_risk_df: Country risk indices
        """
        self.suppliers_df = suppliers_df.copy()
        self.dependencies_df = dependencies_df.copy()
        self.country_risk_df = country_risk_df

        # Normalize ID columns to strings to handle both numeric and string IDs
        self.suppliers_df['id'] = self.suppliers_df['id'].astype(str)
        self.dependencies_df['source_id'] = self.dependencies_df['source_id'].astype(str)
        self.dependencies_df['target_id'] = self.dependencies_df['target_id'].astype(str)
        
        print(f"Loaded {len(suppliers_df)} suppliers")
        print(f"Loaded {len(dependencies_df)} dependencies")
        print(f"Loaded {len(country_risk_df)} countries")
    
    def build_graph(self) -> nx.DiGraph:
        """
        Build the complete network graph.
        
        Returns:
            NetworkX directed graph with suppliers as nodes
        """
        print("\n" + "="*60)
        print("BUILDING SUPPLIER NETWORK GRAPH")
        print("="*60 + "\n")
        
        # Step 1: Add all suppliers as nodes
        self._add_supplier_nodes()
        
        # Step 2: Add country risk data to nodes
        self._add_country_risk_to_nodes()
        
        # Step 3: Add dependency edges
        self._add_dependency_edges()
        
        # Step 4: Calculate network statistics
        self._print_network_stats()
        
        print("\n[PASS] Network graph built successfully!\n")
        
        return self.graph
    
    def _add_supplier_nodes(self) -> None:
        """Add all suppliers as nodes in the graph."""
        print("Adding supplier nodes...")
        
        for _, supplier in self.suppliers_df.iterrows():
            # Add node with supplier ID
            node_id = str(supplier['id'])
            
            # Add all supplier attributes as node properties
            self.graph.add_node(
                node_id,
                name=supplier['name'],
                tier=supplier['tier'],
                component=supplier['component'],
                country=supplier['country'],
                country_code=supplier['country_code'],
                region=supplier['region'],
                contract_value_eur_m=supplier['contract_value_eur_m'],
                lead_time_days=supplier['lead_time_days'],
                financial_health=supplier['financial_health'],
                past_disruptions=supplier['past_disruptions'],
                has_backup=supplier['has_backup']
            )
        
        print(f"[OK] Added {self.graph.number_of_nodes()} nodes")
    
    def _add_country_risk_to_nodes(self) -> None:
        """Add country risk indices to each supplier node."""
        print("Adding country risk data to nodes...")
        
        # Create a lookup dictionary: country_code → risk data
        country_risk_dict = {}
        for _, country in self.country_risk_df.iterrows():
            country_risk_dict[country['country_code']] = {
                'political_stability': country['political_stability'],
                'natural_disaster_freq': country['natural_disaster_freq'],
                'logistics_performance': country['logistics_performance'],
                'trade_restriction_risk': country['trade_restriction_risk']
            }
        
        # Add risk data to each node
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            country_code = node_data['country_code']
            
            # Get risk data for this country
            risk_data = country_risk_dict.get(country_code, {})
            
            # Add risk indices as node attributes
            self.graph.nodes[node_id].update(risk_data)
        
        print(f"[OK] Added country risk data to all nodes")
    
    def _add_dependency_edges(self) -> None:
        """Add dependency relationships as directed edges."""
        print("Adding dependency edges...")
        
        for _, dep in self.dependencies_df.iterrows():
            source = str(dep['source_id'])
            target = str(dep['target_id'])
            weight = dep['dependency_weight']
            
            # Add directed edge: source → target
            self.graph.add_edge(
                source,
                target,
                weight=weight
            )
        
        print(f"[OK] Added {self.graph.number_of_edges()} edges")
    
    def _print_network_stats(self) -> None:
        """Print statistics about the network structure."""
        print("\nNetwork Statistics:")
        print(f"  • Total nodes: {self.graph.number_of_nodes()}")
        print(f"  • Total edges: {self.graph.number_of_edges()}")
        
        # Count by tier
        tier_counts = {}
        for node_id in self.graph.nodes():
            tier = self.graph.nodes[node_id]['tier']
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        print(f"  • Tier-1 nodes: {tier_counts.get(1, 0)}")
        print(f"  • Tier-2 nodes: {tier_counts.get(2, 0)}")
        print(f"  • Tier-3 nodes: {tier_counts.get(3, 0)}")
        
        # Average degree (connections per node)
        avg_out_degree = sum(d for n, d in self.graph.out_degree()) / self.graph.number_of_nodes()
        avg_in_degree = sum(d for n, d in self.graph.in_degree()) / self.graph.number_of_nodes()
        
        print(f"  • Average outgoing connections: {avg_out_degree:.2f}")
        print(f"  • Average incoming connections: {avg_in_degree:.2f}")
    
    def get_tier_suppliers(self, tier: int) -> List[str]:
        """
        Get all supplier IDs for a specific tier.
        
        Args:
            tier: Tier number (1, 2, or 3)
            
        Returns:
            List of supplier IDs in that tier
        """
        return [
            node_id for node_id in self.graph.nodes()
            if self.graph.nodes[node_id]['tier'] == tier
        ]
    
    def get_supplier_dependencies(self, supplier_id: str) -> Dict[str, List[str]]:
        """
        Get all dependencies for a specific supplier.
        
        Args:
            supplier_id: Supplier ID to query
            
        Returns:
            Dictionary with 'upstream' (who feeds this supplier) and
            'downstream' (who this supplier feeds)
        """
        return {
            'upstream': list(self.graph.predecessors(supplier_id)),
            'downstream': list(self.graph.successors(supplier_id))
        }
    
    def get_node_attributes(self, supplier_id: str) -> Dict:
        """
        Get all attributes for a specific supplier node.
        
        Args:
            supplier_id: Supplier ID
            
        Returns:
            Dictionary of all node attributes
        """
        return dict(self.graph.nodes[supplier_id])