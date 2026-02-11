"""
Recommendation engine for SupplierShield.

This module generates rule-based actionable recommendations for
supply chain risk mitigation.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple


class RecommendationEngine:
    """
    Rule-based recommendation engine.
    
    Generates prioritized, actionable recommendations based on:
    - Risk scores (propagated)
    - SPOF status
    - Revenue exposure
    - Contract value
    - Regional concentration
    """
    
    def __init__(self,
                 graph: nx.DiGraph,
                 product_bom_df: pd.DataFrame):
        """
        Initialize the recommendation engine.
        
        Args:
            graph: NetworkX graph with risk scores and SPOF flags
            product_bom_df: Product BOM data
        """
        self.graph = graph
        self.product_bom_df = product_bom_df
        
        # Recommendation rules configuration
        self.rules = self._define_rules()
    
    def _define_rules(self) -> List[Dict]:
        """
        Define recommendation rules.
        
        Each rule has:
        - name: Rule identifier
        - condition: Function that returns True if rule applies
        - severity: CRITICAL, HIGH, MEDIUM, WATCH
        - action: What to do
        - timeline: Timeframe for action (days)
        
        Returns:
            List of rule definitions
        """
        return [
            {
                'name': 'R1_CRITICAL_NO_BACKUP',
                'severity': 'CRITICAL',
                'action_template': 'Qualify alternative supplier immediately for {component}',
                'timeline': '0-30 days',
                'priority': 1
            },
            {
                'name': 'R2_SPOF_HIGH_RISK',
                'severity': 'HIGH',
                'action_template': 'Establish dual-sourcing for {component}',
                'timeline': '30-60 days',
                'priority': 2
            },
            {
                'name': 'R3_HIGH_VALUE_NO_BACKUP',
                'severity': 'HIGH',
                'action_template': 'Establish backup for high-value dependency: {component}',
                'timeline': '30-60 days',
                'priority': 3
            },
            {
                'name': 'R4_FINANCIAL_HEALTH',
                'severity': 'WATCH',
                'action_template': 'Monitor supplier financial stability for {component}',
                'timeline': 'Ongoing',
                'priority': 4
            },
            {
                'name': 'R5_MEDIUM_RISK_NO_BACKUP',
                'severity': 'MEDIUM',
                'action_template': 'Consider backup qualification for {component}',
                'timeline': '60-90 days',
                'priority': 5
            }
        ]
    
    def generate_all_recommendations(self) -> List[Dict]:
        """
        Generate all recommendations for the supplier network.
        
        Returns:
            List of recommendation dictionaries
        """
        print("\n" + "="*60)
        print("GENERATING RECOMMENDATIONS")
        print("="*60 + "\n")
        
        print("Analyzing all suppliers against rule set...")
        
        recommendations = []
        
        for node_id in self.graph.nodes():
            node_recs = self._generate_supplier_recommendations(node_id)
            recommendations.extend(node_recs)
        
        # Sort by priority and impact
        recommendations.sort(
            key=lambda x: (
                self._severity_rank(x['severity']),
                -x.get('impact_score', 0)
            )
        )
        
        print(f"[OK] Generated {len(recommendations)} recommendations\n")
        
        return recommendations
    
    def _severity_rank(self, severity: str) -> int:
        """Convert severity to numeric rank for sorting."""
        ranks = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'WATCH': 3}
        return ranks.get(severity, 4)
    
    def _generate_supplier_recommendations(self, supplier_id: str) -> List[Dict]:
        """
        Generate recommendations for a single supplier.
        
        Args:
            supplier_id: Supplier to analyze
            
        Returns:
            List of recommendations for this supplier
        """
        node_data = self.graph.nodes[supplier_id]
        recommendations = []
        
        # Get key attributes
        propagated_risk = node_data.get('risk_propagated', node_data['risk_composite'])
        has_backup = node_data.get('has_backup', False)
        is_spof = node_data.get('is_spof', False)
        financial_health = node_data.get('financial_health', 100)
        contract_value = node_data.get('contract_value_eur_m', 0)
        
        # Rule 1: Critical risk + no backup
        if propagated_risk >= 75 and not has_backup:
            recommendations.append(self._create_recommendation(
                supplier_id=supplier_id,
                rule_name='R1_CRITICAL_NO_BACKUP',
                severity='CRITICAL',
                action=f"Qualify alternative supplier immediately for {node_data['component']}",
                reason=f"CRITICAL risk ({propagated_risk:.1f}) with no backup supplier",
                timeline='0-30 days',
                impact_score=propagated_risk * contract_value
            ))
        
        # Rule 2: SPOF + high risk
        if is_spof and propagated_risk >= 55:
            recommendations.append(self._create_recommendation(
                supplier_id=supplier_id,
                rule_name='R2_SPOF_HIGH_RISK',
                severity='HIGH',
                action=f"Establish dual-sourcing for {node_data['component']}",
                reason=f"Single point of failure with HIGH risk ({propagated_risk:.1f})",
                timeline='30-60 days',
                impact_score=propagated_risk * contract_value * 1.5  # SPOF multiplier
            ))
        
        # Rule 3: High contract value + high risk + no backup
        if propagated_risk >= 55 and contract_value >= 2.0 and not has_backup:
            recommendations.append(self._create_recommendation(
                supplier_id=supplier_id,
                rule_name='R3_HIGH_VALUE_NO_BACKUP',
                severity='HIGH',
                action=f"Establish backup for high-value dependency: {node_data['component']}",
                reason=f"€{contract_value:.1f}M contract + HIGH risk ({propagated_risk:.1f}) + no backup",
                timeline='30-60 days',
                impact_score=contract_value * 10
            ))
        
        # Rule 4: Poor financial health
        if financial_health < 35:
            recommendations.append(self._create_recommendation(
                supplier_id=supplier_id,
                rule_name='R4_FINANCIAL_HEALTH',
                severity='WATCH',
                action=f"Monitor supplier financial stability for {node_data['component']}",
                reason=f"Low financial health score ({financial_health})",
                timeline='Ongoing',
                impact_score=contract_value
            ))
        
        # Rule 5: Medium risk + no backup
        if 45 <= propagated_risk < 55 and not has_backup:
            recommendations.append(self._create_recommendation(
                supplier_id=supplier_id,
                rule_name='R5_MEDIUM_RISK_NO_BACKUP',
                severity='MEDIUM',
                action=f"Consider backup qualification for {node_data['component']}",
                reason=f"MEDIUM risk ({propagated_risk:.1f}) with no backup",
                timeline='60-90 days',
                impact_score=propagated_risk
            ))
        
        return recommendations
    
    def _create_recommendation(self,
                               supplier_id: str,
                               rule_name: str,
                               severity: str,
                               action: str,
                               reason: str,
                               timeline: str,
                               impact_score: float) -> Dict:
        """Create a recommendation dictionary."""
        node_data = self.graph.nodes[supplier_id]
        
        return {
            'supplier_id': supplier_id,
            'supplier_name': node_data['name'],
            'tier': node_data['tier'],
            'country': node_data['country'],
            'component': node_data['component'],
            'rule_name': rule_name,
            'severity': severity,
            'action': action,
            'reason': reason,
            'timeline': timeline,
            'impact_score': impact_score,
            'propagated_risk': node_data.get('risk_propagated', node_data['risk_composite']),
            'contract_value': node_data['contract_value_eur_m']
        }
    
    def generate_regional_recommendations(self) -> List[Dict]:
        """
        Generate regional concentration recommendations.
        
        Returns:
            List of regional recommendations
        """
        print("\n" + "="*60)
        print("ANALYZING REGIONAL CONCENTRATION")
        print("="*60 + "\n")
        
        # Count suppliers by region for Tier-1 and Tier-2
        region_counts = {}
        total_tier12 = 0
        
        for node_id in self.graph.nodes():
            tier = self.graph.nodes[node_id]['tier']
            if tier in [1, 2]:
                region = self.graph.nodes[node_id]['region']
                region_counts[region] = region_counts.get(region, 0) + 1
                total_tier12 += 1
        
        recommendations = []
        
        # Check for >40% concentration
        for region, count in region_counts.items():
            concentration = (count / total_tier12) * 100
            
            if concentration > 40:
                recommendations.append({
                    'type': 'regional_concentration',
                    'severity': 'MEDIUM',
                    'region': region,
                    'concentration': concentration,
                    'supplier_count': count,
                    'action': f"Diversify sourcing away from {region}",
                    'reason': f"{concentration:.1f}% of Tier-1/2 suppliers concentrated in {region}",
                    'timeline': '60-90 days'
                })
        
        if recommendations:
            print(f"Found {len(recommendations)} regional concentration risks\n")
        else:
            print("No regional concentration risks detected\n")
        
        return recommendations
    
    def print_recommendations(self, recommendations: List[Dict]) -> None:
        """
        Print recommendations in a formatted way.
        
        Args:
            recommendations: List of recommendation dictionaries
        """
        if not recommendations:
            print("No recommendations generated.")
            return
        
        print("\n" + "="*60)
        print("ACTIONABLE RECOMMENDATIONS")
        print("="*60 + "\n")
        
        # Group by severity
        by_severity = {}
        for rec in recommendations:
            severity = rec['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(rec)
        
        # Print summary
        print("Summary:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']:
            if severity in by_severity:
                print(f"  • {severity}: {len(by_severity[severity])} recommendations")
        print()
        
        # Print detailed recommendations
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']:
            if severity not in by_severity:
                continue
            
            emoji = {'CRITICAL': '[!!]', 'HIGH': '[!]', 'MEDIUM': '[~]', 'WATCH': '[.]'}
            print(f"\n{emoji[severity]} {severity} PRIORITY ({by_severity[severity][0]['timeline']})")
            print("-" * 60)
            
            for i, rec in enumerate(by_severity[severity], 1):
                print(f"\n{i}. {rec['supplier_id']} - {rec['supplier_name']}")
                print(f"   Tier: {rec['tier']} | Component: {rec['component']}")
                print(f"   Country: {rec['country']}")
                print(f"   Action: {rec['action']}")
                print(f"   Reason: {rec['reason']}")
                print(f"   Risk: {rec['propagated_risk']:.1f} | Contract: €{rec['contract_value']:.2f}M")
    
    def export_to_dataframe(self, recommendations: List[Dict]) -> pd.DataFrame:
        """
        Export recommendations to DataFrame for analysis.
        
        Args:
            recommendations: List of recommendations
            
        Returns:
            DataFrame with recommendations
        """
        if not recommendations:
            return pd.DataFrame()
        
        df = pd.DataFrame(recommendations)
        
        # Select key columns
        columns = [
            'severity', 'supplier_id', 'supplier_name', 'tier', 
            'country', 'component', 'action', 'reason', 
            'timeline', 'propagated_risk', 'contract_value'
        ]
        
        df = df[columns]
        
        return df
    
    def generate_executive_summary(self, recommendations: List[Dict]) -> Dict:
        """
        Generate executive summary of recommendations.
        
        Args:
            recommendations: List of recommendations
            
        Returns:
            Dictionary with executive summary
        """
        # Count by severity
        severity_counts = {}
        for rec in recommendations:
            severity = rec['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Total contract value at risk
        critical_value = sum(
            rec['contract_value'] 
            for rec in recommendations 
            if rec['severity'] == 'CRITICAL'
        )
        
        high_value = sum(
            rec['contract_value'] 
            for rec in recommendations 
            if rec['severity'] == 'HIGH'
        )
        
        # Unique suppliers
        unique_suppliers = len(set(rec['supplier_id'] for rec in recommendations))
        
        # Countries affected
        unique_countries = len(set(rec['country'] for rec in recommendations))
        
        return {
            'total_recommendations': len(recommendations),
            'critical_count': severity_counts.get('CRITICAL', 0),
            'high_count': severity_counts.get('HIGH', 0),
            'medium_count': severity_counts.get('MEDIUM', 0),
            'watch_count': severity_counts.get('WATCH', 0),
            'critical_contract_value': critical_value,
            'high_contract_value': high_value,
            'unique_suppliers': unique_suppliers,
            'unique_countries': unique_countries
        }