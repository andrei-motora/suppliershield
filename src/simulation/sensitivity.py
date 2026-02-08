"""
Sensitivity analysis for SupplierShield.

This module ranks suppliers by criticality - which single supplier
failure would cause the most damage to the portfolio.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple
import numpy as np


class SensitivityAnalyzer:
    """
    Sensitivity analyzer for supplier criticality ranking.
    
    Answers: "Which single supplier failure would cause the most damage?"
    
    Criticality = (risk / 100) × revenue_exposure
    """
    
    def __init__(self, 
                 graph: nx.DiGraph,
                 product_bom_df: pd.DataFrame):
        """
        Initialize the sensitivity analyzer.
        
        Args:
            graph: NetworkX graph with risk scores
            product_bom_df: Product BOM data
        """
        self.graph = graph
        self.product_bom_df = product_bom_df
        
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
    
    def calculate_criticality_ranking(self) -> pd.DataFrame:
        """
        Calculate criticality ranking for all suppliers.
        
        Returns:
            DataFrame with criticality scores, sorted by criticality descending
        """
        print("\n" + "="*60)
        print("CALCULATING SUPPLIER CRITICALITY RANKING")
        print("="*60 + "\n")
        
        print("Analyzing all 120 suppliers...")
        print("Calculating: Criticality = Risk × Revenue Exposure\n")
        
        results = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            
            # Get propagated risk (or composite if propagation not done)
            propagated_risk = node_data.get(
                'risk_propagated',
                node_data['risk_composite']
            )
            
            # Calculate revenue exposure
            exposure = self._calculate_revenue_exposure(node_id)
            
            # Calculate criticality
            criticality = (propagated_risk / 100.0) * exposure['total_exposure']
            
            results.append({
                'supplier_id': node_id,
                'name': node_data['name'],
                'tier': node_data['tier'],
                'country': node_data['country'],
                'component': node_data['component'],
                'contract_value_eur_m': node_data['contract_value_eur_m'],
                'propagated_risk': propagated_risk,
                'risk_category': node_data.get('risk_category', 'UNKNOWN'),
                'direct_revenue_exposure': exposure['direct_revenue'],
                'indirect_revenue_exposure': exposure['indirect_revenue'],
                'total_revenue_exposure': exposure['total_exposure'],
                'criticality_score': criticality,
                'affected_products': exposure['affected_products'],
                'downstream_suppliers': exposure['downstream_count']
            })
        
        # Convert to DataFrame and sort by criticality
        df = pd.DataFrame(results)
        df = df.sort_values('criticality_score', ascending=False)
        df = df.reset_index(drop=True)
        df.index = df.index + 1  # Start ranking from 1
        
        print("✓ Criticality calculated for all suppliers")
        
        return df
    
    def _calculate_revenue_exposure(self, supplier_id: str) -> Dict:
        """
        Calculate revenue exposure if this supplier fails.
        
        Args:
            supplier_id: Supplier to analyze
            
        Returns:
            Dictionary with direct, indirect, and total exposure
        """
        # Direct exposure: products that directly depend on this supplier
        direct_products = []
        direct_revenue = 0.0
        
        for product_id, product_data in self.product_supplier_map.items():
            if supplier_id in product_data['suppliers']:
                direct_products.append(product_id)
                direct_revenue += product_data['revenue']
        
        # Indirect exposure: downstream suppliers and their products
        indirect_revenue = 0.0
        downstream_suppliers = set()
        
        try:
            # Get all descendants (suppliers downstream)
            descendants = nx.descendants(self.graph, supplier_id)
            downstream_suppliers = descendants
            
            # Find products depending on downstream suppliers
            for desc_id in descendants:
                for product_id, product_data in self.product_supplier_map.items():
                    if desc_id in product_data['suppliers']:
                        # Only count if not already in direct
                        if product_id not in direct_products:
                            indirect_revenue += product_data['revenue']
        except:
            # No descendants
            pass
        
        # Weight indirect revenue (50% because cascading failures are uncertain)
        weighted_indirect = indirect_revenue * 0.5
        
        return {
            'direct_revenue': direct_revenue,
            'indirect_revenue': indirect_revenue,
            'weighted_indirect': weighted_indirect,
            'total_exposure': direct_revenue + weighted_indirect,
            'affected_products': len(direct_products),
            'downstream_count': len(downstream_suppliers)
        }
    
    def get_top_critical(self, n: int = 20) -> pd.DataFrame:
        """
        Get top N most critical suppliers.
        
        Args:
            n: Number of top suppliers to return
            
        Returns:
            DataFrame with top N suppliers
        """
        full_ranking = self.calculate_criticality_ranking()
        return full_ranking.head(n)
    
    def print_top_critical(self, n: int = 20) -> None:
        """
        Print top N most critical suppliers with detailed breakdown.
        
        Args:
            n: Number of suppliers to display
        """
        top_df = self.get_top_critical(n)
        
        print("\n" + "="*60)
        print(f"TOP {n} MOST CRITICAL SUPPLIERS")
        print("="*60 + "\n")
        
        for idx, row in top_df.iterrows():
            print(f"{idx}. {row['supplier_id']} - {row['name']}")
            print(f"   Tier: {row['tier']} | Component: {row['component']}")
            print(f"   Country: {row['country']}")
            print(f"   Risk: {row['propagated_risk']:.1f} ({row['risk_category']})")
            print(f"   Direct Revenue Exposure: €{row['direct_revenue_exposure']:.2f}M")
            print(f"   Indirect Revenue Exposure: €{row['indirect_revenue_exposure']:.2f}M")
            print(f"   Total Exposure: €{row['total_revenue_exposure']:.2f}M")
            print(f"   Criticality Score: {row['criticality_score']:.2f}")
            print(f"   Affected Products: {row['affected_products']}")
            print(f"   Downstream Suppliers: {row['downstream_suppliers']}")
            print()
    
    def analyze_by_tier(self) -> pd.DataFrame:
        """
        Analyze criticality by tier.
        
        Returns:
            DataFrame with tier-level statistics
        """
        full_ranking = self.calculate_criticality_ranking()
        
        tier_stats = []
        
        for tier in [1, 2, 3]:
            tier_df = full_ranking[full_ranking['tier'] == tier]
            
            tier_stats.append({
                'Tier': tier,
                'Count': len(tier_df),
                'Avg Criticality': tier_df['criticality_score'].mean(),
                'Max Criticality': tier_df['criticality_score'].max(),
                'Avg Risk': tier_df['propagated_risk'].mean(),
                'Avg Exposure (€M)': tier_df['total_revenue_exposure'].mean()
            })
        
        return pd.DataFrame(tier_stats)
    
    def analyze_by_country(self, top_n: int = 10) -> pd.DataFrame:
        """
        Analyze criticality by country.
        
        Args:
            top_n: Number of top countries to return
            
        Returns:
            DataFrame with country-level statistics
        """
        full_ranking = self.calculate_criticality_ranking()
        
        country_stats = full_ranking.groupby('country').agg({
            'criticality_score': ['sum', 'mean', 'max'],
            'supplier_id': 'count',
            'propagated_risk': 'mean',
            'total_revenue_exposure': 'sum'
        }).round(2)
        
        country_stats.columns = [
            'Total Criticality',
            'Avg Criticality',
            'Max Criticality',
            'Supplier Count',
            'Avg Risk',
            'Total Exposure (€M)'
        ]
        
        country_stats = country_stats.sort_values('Total Criticality', ascending=False)
        
        return country_stats.head(top_n)
    
    def identify_critical_clusters(self, 
                                   criticality_threshold: float = 10.0) -> Dict:
        """
        Identify clusters of critical suppliers.
        
        Args:
            criticality_threshold: Minimum criticality to be considered critical
            
        Returns:
            Dictionary with cluster analysis
        """
        full_ranking = self.calculate_criticality_ranking()
        critical_df = full_ranking[
            full_ranking['criticality_score'] >= criticality_threshold
        ]
        
        # Group by country
        country_clusters = critical_df.groupby('country').agg({
            'supplier_id': 'count',
            'criticality_score': 'sum',
            'total_revenue_exposure': 'sum'
        }).round(2)
        
        country_clusters.columns = [
            'Critical Suppliers',
            'Total Criticality',
            'Total Exposure (€M)'
        ]
        
        country_clusters = country_clusters.sort_values(
            'Total Criticality',
            ascending=False
        )
        
        # Group by tier
        tier_clusters = critical_df.groupby('tier').agg({
            'supplier_id': 'count',
            'criticality_score': 'sum'
        }).round(2)
        
        tier_clusters.columns = ['Critical Suppliers', 'Total Criticality']
        
        return {
            'total_critical': len(critical_df),
            'threshold': criticality_threshold,
            'by_country': country_clusters,
            'by_tier': tier_clusters,
            'critical_suppliers': critical_df['supplier_id'].tolist()
        }
    
    def compare_risk_vs_exposure(self) -> pd.DataFrame:
        """
        Compare suppliers with high risk but low exposure vs 
        low risk but high exposure.
        
        Returns:
            DataFrame with categorized suppliers
        """
        full_ranking = self.calculate_criticality_ranking()
        
        # Define thresholds
        high_risk_threshold = 60.0
        high_exposure_threshold = full_ranking['total_revenue_exposure'].quantile(0.75)
        
        # Categorize
        categories = []
        
        for _, row in full_ranking.iterrows():
            risk = row['propagated_risk']
            exposure = row['total_revenue_exposure']
            
            if risk >= high_risk_threshold and exposure >= high_exposure_threshold:
                category = 'High Risk & High Exposure (CRITICAL)'
            elif risk >= high_risk_threshold and exposure < high_exposure_threshold:
                category = 'High Risk & Low Exposure (Monitor)'
            elif risk < high_risk_threshold and exposure >= high_exposure_threshold:
                category = 'Low Risk & High Exposure (SPOF Candidate)'
            else:
                category = 'Low Risk & Low Exposure (OK)'
            
            categories.append({
                'supplier_id': row['supplier_id'],
                'name': row['name'],
                'risk': risk,
                'exposure': exposure,
                'criticality': row['criticality_score'],
                'category': category
            })
        
        cat_df = pd.DataFrame(categories)
        cat_df = cat_df.sort_values('criticality', ascending=False)
        
        return cat_df
    
    def get_pareto_analysis(self) -> Dict:
        """
        Perform Pareto analysis: what % of suppliers account for 80% of criticality?
        
        Returns:
            Dictionary with Pareto analysis results
        """
        full_ranking = self.calculate_criticality_ranking()
        
        # Calculate cumulative criticality
        total_criticality = full_ranking['criticality_score'].sum()
        full_ranking['cumulative_criticality'] = full_ranking['criticality_score'].cumsum()
        full_ranking['cumulative_percent'] = (
            full_ranking['cumulative_criticality'] / total_criticality * 100
        )
        
        # Find 80% threshold
        pareto_80_count = (full_ranking['cumulative_percent'] <= 80).sum()
        pareto_80_percent = (pareto_80_count / len(full_ranking)) * 100
        
        # Find 50% threshold
        pareto_50_count = (full_ranking['cumulative_percent'] <= 50).sum()
        pareto_50_percent = (pareto_50_count / len(full_ranking)) * 100
        
        return {
            'total_suppliers': len(full_ranking),
            'total_criticality': total_criticality,
            'pareto_80_suppliers': pareto_80_count,
            'pareto_80_percent': pareto_80_percent,
            'pareto_50_suppliers': pareto_50_count,
            'pareto_50_percent': pareto_50_percent,
            'top_10_criticality': full_ranking.head(10)['criticality_score'].sum(),
            'top_10_percent': (
                full_ranking.head(10)['criticality_score'].sum() / total_criticality * 100
            )
        }