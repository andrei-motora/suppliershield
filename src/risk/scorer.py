"""
Risk scoring engine for SupplierShield.

This module calculates composite risk scores for each supplier based on
5 weighted dimensions.
"""

import networkx as nx
import pandas as pd
from typing import Dict, Tuple
import numpy as np

from .config import (
    RISK_WEIGHTS,
    CONCENTRATION_THRESHOLDS,
    get_risk_category
)


class RiskScorer:
    """
    Calculates multi-dimensional risk scores for suppliers.
    
    Combines 5 risk dimensions into a single composite score:
    1. Geopolitical risk (from country data)
    2. Natural disaster risk (from country data)
    3. Financial risk (from supplier's financial health)
    4. Logistics risk (from country's infrastructure)
    5. Concentration risk (from network graph structure)
    """
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialize the risk scorer.
        
        Args:
            graph: NetworkX graph with supplier nodes
        """
        self.graph = graph
        self.risk_scores = {}  # Will store {supplier_id: {dimension: score}}
    
    def calculate_all_risks(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate risk scores for all suppliers.
        
        Returns:
            Dictionary mapping supplier_id to risk breakdown:
            {
                'S001': {
                    'geopolitical': 45.0,
                    'natural_disaster': 55.0,
                    'financial': 30.0,
                    'logistics': 20.0,
                    'concentration': 60.0,
                    'composite': 42.5,
                    'category': 'MEDIUM'
                },
                ...
            }
        """
        print("\n" + "="*60)
        print("CALCULATING RISK SCORES")
        print("="*60 + "\n")
        
        print("Calculating risk dimensions for all suppliers...")
        
        for node_id in self.graph.nodes():
            # Calculate each dimension
            geo_risk = self._calculate_geopolitical_risk(node_id)
            disaster_risk = self._calculate_natural_disaster_risk(node_id)
            financial_risk = self._calculate_financial_risk(node_id)
            logistics_risk = self._calculate_logistics_risk(node_id)
            concentration_risk = self._calculate_concentration_risk(node_id)
            
            # Calculate composite score (weighted average)
            composite = (
                geo_risk * RISK_WEIGHTS['geopolitical'] +
                disaster_risk * RISK_WEIGHTS['natural_disaster'] +
                financial_risk * RISK_WEIGHTS['financial'] +
                logistics_risk * RISK_WEIGHTS['logistics'] +
                concentration_risk * RISK_WEIGHTS['concentration']
            )
            
            # Clamp to 0-100 range
            composite = np.clip(composite, 0, 100)
            
            # Get category
            category = get_risk_category(composite)
            
            # Store all scores
            self.risk_scores[node_id] = {
                'geopolitical': round(geo_risk, 2),
                'natural_disaster': round(disaster_risk, 2),
                'financial': round(financial_risk, 2),
                'logistics': round(logistics_risk, 2),
                'concentration': round(concentration_risk, 2),
                'composite': round(composite, 2),
                'category': category
            }
        
        print(f"✓ Calculated risk scores for {len(self.risk_scores)} suppliers")
        
        # Print summary statistics
        self._print_risk_summary()
        
        return self.risk_scores
    
    def _calculate_geopolitical_risk(self, node_id: str) -> float:
        """
        Calculate geopolitical risk from country political stability.
        
        Args:
            node_id: Supplier ID
            
        Returns:
            Geopolitical risk score (0-100)
        """
        # Get country political stability index from node
        # Higher political_stability value = more risk
        political_stability = self.graph.nodes[node_id].get('political_stability', 50)
        
        return float(political_stability)
    
    def _calculate_natural_disaster_risk(self, node_id: str) -> float:
        """
        Calculate natural disaster risk from country disaster frequency.
        
        Args:
            node_id: Supplier ID
            
        Returns:
            Natural disaster risk score (0-100)
        """
        # Get country natural disaster frequency from node
        disaster_freq = self.graph.nodes[node_id].get('natural_disaster_freq', 50)
        
        return float(disaster_freq)
    
    def _calculate_financial_risk(self, node_id: str) -> float:
        """
        Calculate financial risk (inverse of financial health).
        
        Args:
            node_id: Supplier ID
            
        Returns:
            Financial risk score (0-100)
        """
        # Get supplier's financial health (0-100, higher = healthier)
        financial_health = self.graph.nodes[node_id].get('financial_health', 50)
        
        # Invert: low health = high risk
        financial_risk = 100 - financial_health
        
        return float(financial_risk)
    
    def _calculate_logistics_risk(self, node_id: str) -> float:
        """
        Calculate logistics risk (inverse of logistics performance).
        
        Args:
            node_id: Supplier ID
            
        Returns:
            Logistics risk score (0-100)
        """
        # Get country logistics performance (0-100, higher = better)
        logistics_performance = self.graph.nodes[node_id].get('logistics_performance', 50)
        
        # Invert: poor infrastructure = high risk
        logistics_risk = 100 - logistics_performance
        
        return float(logistics_risk)
    
    def _calculate_concentration_risk(self, node_id: str) -> float:
        """
        Calculate concentration risk based on number of backup suppliers.
        
        Suppliers with few alternatives are riskier.
        
        Args:
            node_id: Supplier ID
            
        Returns:
            Concentration risk score (0-100)
        """
        # Count how many suppliers feed INTO this one (incoming edges)
        incoming_edges = list(self.graph.predecessors(node_id))
        num_suppliers = len(incoming_edges)
        
        # Get supplier's tier
        tier = self.graph.nodes[node_id]['tier']
        
        # Calculate concentration risk
        if num_suppliers <= 1:
            # Very few suppliers = high concentration risk
            if tier == 1:
                # Tier-1 with no backup is especially risky
                risk = CONCENTRATION_THRESHOLDS['tier_1_high_risk']
            else:
                risk = CONCENTRATION_THRESHOLDS['tier_2_3_high_risk']
        else:
            # More suppliers = lower concentration risk
            # Each additional supplier reduces risk
            base = CONCENTRATION_THRESHOLDS['tier_2_3_high_risk']
            reduction = CONCENTRATION_THRESHOLDS['reduction_per_supplier']
            risk = max(
                CONCENTRATION_THRESHOLDS['base_risk'],
                base - (num_suppliers * reduction)
            )
        
        return float(risk)
    
    def _print_risk_summary(self) -> None:
        """Print summary statistics about calculated risks."""
        print("\nRisk Score Summary:")
        
        # Get all composite scores
        composites = [s['composite'] for s in self.risk_scores.values()]
        
        print(f"  • Average risk score: {np.mean(composites):.2f}")
        print(f"  • Min risk score: {np.min(composites):.2f}")
        print(f"  • Max risk score: {np.max(composites):.2f}")
        print(f"  • Median risk score: {np.median(composites):.2f}")
        
        # Count by category
        categories = [s['category'] for s in self.risk_scores.values()]
        category_counts = {
            'LOW': categories.count('LOW'),
            'MEDIUM': categories.count('MEDIUM'),
            'HIGH': categories.count('HIGH'),
            'CRITICAL': categories.count('CRITICAL')
        }
        
        print(f"\nRisk Categories:")
        print(f"  • LOW (0-34): {category_counts['LOW']} suppliers")
        print(f"  • MEDIUM (35-54): {category_counts['MEDIUM']} suppliers")
        print(f"  • HIGH (55-74): {category_counts['HIGH']} suppliers")
        print(f"  • CRITICAL (75-100): {category_counts['CRITICAL']} suppliers")
    
    def get_supplier_risk(self, supplier_id: str) -> Dict[str, float]:
        """
        Get risk breakdown for a specific supplier.
        
        Args:
            supplier_id: Supplier ID
            
        Returns:
            Dictionary with all risk dimensions and composite score
        """
        return self.risk_scores.get(supplier_id, {})
    
    def get_high_risk_suppliers(self, threshold: float = 55.0) -> Dict[str, Dict]:
        """
        Get all suppliers above a risk threshold.
        
        Args:
            threshold: Minimum risk score to include (default: 55 = HIGH)
            
        Returns:
            Dictionary of high-risk suppliers with their scores
        """
        return {
            sid: scores
            for sid, scores in self.risk_scores.items()
            if scores['composite'] >= threshold
        }
    
    def add_scores_to_graph(self) -> None:
        """
        Add calculated risk scores as node attributes in the graph.
        
        This makes risk scores accessible directly from graph nodes.
        """
        print("\nAdding risk scores to graph nodes...")
        
        for node_id, scores in self.risk_scores.items():
            # Add all risk dimensions as node attributes
            self.graph.nodes[node_id]['risk_geopolitical'] = scores['geopolitical']
            self.graph.nodes[node_id]['risk_natural_disaster'] = scores['natural_disaster']
            self.graph.nodes[node_id]['risk_financial'] = scores['financial']
            self.graph.nodes[node_id]['risk_logistics'] = scores['logistics']
            self.graph.nodes[node_id]['risk_concentration'] = scores['concentration']
            self.graph.nodes[node_id]['risk_composite'] = scores['composite']
            self.graph.nodes[node_id]['risk_category'] = scores['category']
        
        print(f"✓ Added risk scores to all graph nodes")