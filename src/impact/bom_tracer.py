"""
BOM (Bill of Materials) impact tracer for SupplierShield.

This module traces how supplier failures cascade to affect products
and revenue through the Bill of Materials.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Set, Tuple


class BOMImpactTracer:
    """
    BOM Impact Tracer - maps supplier failures to product revenue impact.
    
    Answers: "If Supplier X fails, which products are affected and 
    how much revenue is at risk?"
    """
    
    def __init__(self,
                 graph: nx.DiGraph,
                 product_bom_df: pd.DataFrame):
        """
        Initialize the BOM impact tracer.
        
        Args:
            graph: NetworkX graph with supplier network
            product_bom_df: Product BOM data
        """
        self.graph = graph
        self.product_bom_df = product_bom_df
        
        # Build mappings
        self._build_product_supplier_map()
        self._build_supplier_product_map()
    
    def _build_product_supplier_map(self) -> None:
        """Build mapping: product → suppliers."""
        self.product_supplier_map = {}
        
        for _, product in self.product_bom_df.iterrows():
            product_id = product['product_id']
            supplier_ids = product['component_supplier_ids'].split(',')
            
            self.product_supplier_map[product_id] = {
                'name': product['product_name'],
                'revenue': product['annual_revenue_eur_m'],
                'suppliers': set(supplier_ids)
            }
    
    def _build_supplier_product_map(self) -> None:
        """Build reverse mapping: supplier → products."""
        self.supplier_product_map = {}
        
        for supplier_id in self.graph.nodes():
            self.supplier_product_map[supplier_id] = []
        
        for product_id, product_data in self.product_supplier_map.items():
            for supplier_id in product_data['suppliers']:
                if supplier_id in self.supplier_product_map:
                    self.supplier_product_map[supplier_id].append({
                        'product_id': product_id,
                        'product_name': product_data['name'],
                        'revenue': product_data['revenue']
                    })
    
    def trace_supplier_impact(self, supplier_id: str) -> Dict:
        """
        Trace the impact of a single supplier failure.
        
        Args:
            supplier_id: Supplier that fails
            
        Returns:
            Dictionary with detailed impact analysis
        """
        if supplier_id not in self.graph.nodes():
            return {'error': f'Supplier {supplier_id} not found in network'}
        
        print(f"\n{'='*60}")
        print(f"TRACING BOM IMPACT: {supplier_id}")
        print(f"{'='*60}\n")
        
        supplier_name = self.graph.nodes[supplier_id]['name']
        supplier_tier = self.graph.nodes[supplier_id]['tier']
        
        print(f"Supplier: {supplier_name}")
        print(f"Tier: {supplier_tier}")
        print()
        
        # Get all affected suppliers (this one + downstream)
        affected_suppliers = {supplier_id}
        try:
            descendants = nx.descendants(self.graph, supplier_id)
            affected_suppliers.update(descendants)
        except:
            pass
        
        print(f"Total affected suppliers: {len(affected_suppliers)}")
        print(f"  • Direct: 1 ({supplier_id})")
        print(f"  • Downstream cascade: {len(affected_suppliers) - 1}")
        print()
        
        # Find all affected products
        affected_products = {}
        
        for affected_supplier in affected_suppliers:
            products = self.supplier_product_map.get(affected_supplier, [])
            
            for product in products:
                product_id = product['product_id']
                
                if product_id not in affected_products:
                    affected_products[product_id] = {
                        'name': product['product_name'],
                        'revenue': product['revenue'],
                        'affected_suppliers': [],
                        'total_suppliers': len(self.product_supplier_map[product_id]['suppliers']),
                        'impact_severity': 'Unknown'
                    }
                
                affected_products[product_id]['affected_suppliers'].append(
                    affected_supplier
                )
        
        # Calculate impact severity for each product
        for product_id, product_data in affected_products.items():
            affected_count = len(product_data['affected_suppliers'])
            total_count = product_data['total_suppliers']
            impact_ratio = affected_count / total_count
            
            if impact_ratio >= 0.75:
                severity = 'CRITICAL'  # 75%+ suppliers affected
            elif impact_ratio >= 0.5:
                severity = 'HIGH'  # 50-74% suppliers affected
            elif impact_ratio >= 0.25:
                severity = 'MEDIUM'  # 25-49% suppliers affected
            else:
                severity = 'LOW'  # <25% suppliers affected
            
            product_data['impact_severity'] = severity
            product_data['impact_ratio'] = impact_ratio
        
        # Calculate total revenue at risk
        total_revenue = sum(p['revenue'] for p in affected_products.values())
        
        # Print results
        print(f"Affected Products: {len(affected_products)}")
        print(f"Total Revenue at Risk: €{total_revenue:.2f}M")
        print()
        
        if affected_products:
            print("Product Impact Breakdown:")
            print("-" * 60)
            
            # Sort by severity and revenue
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            sorted_products = sorted(
                affected_products.items(),
                key=lambda x: (severity_order[x[1]['impact_severity']], -x[1]['revenue'])
            )
            
            for product_id, product_data in sorted_products:
                print(f"\n{product_id} - {product_data['name']}")
                print(f"  Annual Revenue: €{product_data['revenue']:.2f}M")
                print(f"  Impact Severity: {product_data['impact_severity']}")
                print(f"  Affected Suppliers: {len(product_data['affected_suppliers'])}/{product_data['total_suppliers']} ({product_data['impact_ratio']*100:.0f}%)")
                print(f"  Failed Suppliers: {', '.join(product_data['affected_suppliers'][:5])}", end='')
                if len(product_data['affected_suppliers']) > 5:
                    print(f" ... +{len(product_data['affected_suppliers']) - 5} more")
                else:
                    print()
        
        return {
            'supplier_id': supplier_id,
            'supplier_name': supplier_name,
            'supplier_tier': supplier_tier,
            'total_affected_suppliers': len(affected_suppliers),
            'direct_impact': 1,
            'cascade_impact': len(affected_suppliers) - 1,
            'affected_products': affected_products,
            'product_count': len(affected_products),
            'total_revenue_at_risk': total_revenue
        }
    
    def trace_multiple_suppliers(self, supplier_ids: List[str]) -> Dict:
        """
        Trace combined impact of multiple supplier failures.
        
        Args:
            supplier_ids: List of suppliers that fail simultaneously
            
        Returns:
            Dictionary with combined impact analysis
        """
        print(f"\n{'='*60}")
        print(f"TRACING COMBINED BOM IMPACT")
        print(f"{'='*60}\n")
        
        print(f"Failed Suppliers: {len(supplier_ids)}")
        for sid in supplier_ids:
            if sid in self.graph.nodes():
                print(f"  • {sid} - {self.graph.nodes[sid]['name']}")
        print()
        
        # Get all affected suppliers
        affected_suppliers = set(supplier_ids)
        
        for supplier_id in supplier_ids:
            try:
                descendants = nx.descendants(self.graph, supplier_id)
                affected_suppliers.update(descendants)
            except:
                pass
        
        print(f"Total affected suppliers: {len(affected_suppliers)}")
        print()
        
        # Find all affected products
        affected_products = {}
        
        for affected_supplier in affected_suppliers:
            products = self.supplier_product_map.get(affected_supplier, [])
            
            for product in products:
                product_id = product['product_id']
                
                if product_id not in affected_products:
                    affected_products[product_id] = {
                        'name': product['product_name'],
                        'revenue': product['revenue'],
                        'affected_suppliers': set()
                    }
                
                affected_products[product_id]['affected_suppliers'].add(
                    affected_supplier
                )
        
        # Calculate total revenue
        total_revenue = sum(p['revenue'] for p in affected_products.values())
        
        print(f"Affected Products: {len(affected_products)}")
        print(f"Total Revenue at Risk: €{total_revenue:.2f}M")
        
        return {
            'failed_suppliers': supplier_ids,
            'total_affected_suppliers': len(affected_suppliers),
            'affected_products': affected_products,
            'product_count': len(affected_products),
            'total_revenue_at_risk': total_revenue
        }
    
    def trace_product_dependencies(self, product_id: str) -> Dict:
        """
        Trace all supplier dependencies for a specific product.
        
        Args:
            product_id: Product to analyze
            
        Returns:
            Dictionary with product dependency analysis
        """
        if product_id not in self.product_supplier_map:
            return {'error': f'Product {product_id} not found'}
        
        product_data = self.product_supplier_map[product_id]
        
        print(f"\n{'='*60}")
        print(f"PRODUCT DEPENDENCY ANALYSIS: {product_id}")
        print(f"{'='*60}\n")
        
        print(f"Product: {product_data['name']}")
        print(f"Annual Revenue: €{product_data['revenue']:.2f}M")
        print()
        
        # Get direct suppliers (Tier-1)
        direct_suppliers = product_data['suppliers']
        
        print(f"Direct Suppliers (Tier-1): {len(direct_suppliers)}")
        
        # Get all upstream suppliers (Tier-2 and Tier-3)
        all_upstream = set()
        
        for tier1_supplier in direct_suppliers:
            if tier1_supplier in self.graph.nodes():
                try:
                    # Get all ancestors (upstream)
                    ancestors = nx.ancestors(self.graph, tier1_supplier)
                    all_upstream.update(ancestors)
                except:
                    pass
        
        print(f"Total Upstream Suppliers: {len(all_upstream)}")
        print(f"Total Supply Chain: {len(direct_suppliers) + len(all_upstream)} suppliers")
        print()
        
        # Analyze by tier
        tier_breakdown = {1: [], 2: [], 3: []}
        
        for supplier_id in direct_suppliers:
            if supplier_id in self.graph.nodes():
                tier_breakdown[1].append(supplier_id)
        
        for supplier_id in all_upstream:
            tier = self.graph.nodes[supplier_id]['tier']
            tier_breakdown[tier].append(supplier_id)
        
        print("Supply Chain by Tier:")
        for tier in [3, 2, 1]:
            print(f"  Tier-{tier}: {len(tier_breakdown[tier])} suppliers")
        
        # Risk analysis
        print("\nRisk Distribution:")
        
        risk_levels = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
        
        all_suppliers = list(direct_suppliers) + list(all_upstream)
        
        for supplier_id in all_suppliers:
            if supplier_id in self.graph.nodes():
                risk_category = self.graph.nodes[supplier_id].get('risk_category', 'UNKNOWN')
                if risk_category in risk_levels:
                    risk_levels[risk_category].append(supplier_id)
        
        for risk_level, suppliers in risk_levels.items():
            if suppliers:
                print(f"  {risk_level}: {len(suppliers)} suppliers")
        
        return {
            'product_id': product_id,
            'product_name': product_data['name'],
            'revenue': product_data['revenue'],
            'direct_suppliers': len(direct_suppliers),
            'upstream_suppliers': len(all_upstream),
            'total_supply_chain': len(all_suppliers),
            'tier_breakdown': {k: len(v) for k, v in tier_breakdown.items()},
            'risk_breakdown': {k: len(v) for k, v in risk_levels.items()}
        }
    
    def identify_critical_products(self) -> pd.DataFrame:
        """
        Identify products with the most supply chain risk.
        
        Returns:
            DataFrame with product risk rankings
        """
        print(f"\n{'='*60}")
        print(f"IDENTIFYING CRITICAL PRODUCTS")
        print(f"{'='*60}\n")
        
        product_risks = []
        
        for product_id, product_data in self.product_supplier_map.items():
            # Get all suppliers in supply chain
            direct_suppliers = product_data['suppliers']
            all_upstream = set()
            
            for tier1_supplier in direct_suppliers:
                if tier1_supplier in self.graph.nodes():
                    try:
                        ancestors = nx.ancestors(self.graph, tier1_supplier)
                        all_upstream.update(ancestors)
                    except:
                        pass
            
            all_suppliers = list(direct_suppliers) + list(all_upstream)
            
            # Calculate average risk
            total_risk = 0.0
            count = 0
            
            for supplier_id in all_suppliers:
                if supplier_id in self.graph.nodes():
                    risk = self.graph.nodes[supplier_id].get(
                        'risk_propagated',
                        self.graph.nodes[supplier_id]['risk_composite']
                    )
                    total_risk += risk
                    count += 1
            
            avg_risk = total_risk / count if count > 0 else 0
            
            # Count high-risk suppliers
            high_risk_count = sum(
                1 for sid in all_suppliers
                if sid in self.graph.nodes() 
                and self.graph.nodes[sid].get('risk_propagated', 
                    self.graph.nodes[sid]['risk_composite']) >= 60
            )
            
            # Calculate product risk score
            product_risk_score = avg_risk * (product_data['revenue'] / 10)
            
            product_risks.append({
                'product_id': product_id,
                'product_name': product_data['name'],
                'revenue': product_data['revenue'],
                'supply_chain_size': len(all_suppliers),
                'avg_supplier_risk': avg_risk,
                'high_risk_suppliers': high_risk_count,
                'product_risk_score': product_risk_score
            })
        
        df = pd.DataFrame(product_risks)
        df = df.sort_values('product_risk_score', ascending=False)
        df = df.reset_index(drop=True)
        df.index = df.index + 1
        
        print("✓ Product risk analysis complete\n")
        
        return df