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

        # Normalize tier to int (CSV may deliver strings like '2')
        self.suppliers_df['tier'] = (
            pd.to_numeric(self.suppliers_df['tier'], errors='coerce')
            .fillna(1)
            .astype(int)
        )

        # Normalize has_backup to bool (CSV may deliver 'yes'/'no'/'true'/'false')
        self.suppliers_df['has_backup'] = (
            self.suppliers_df['has_backup'].apply(self._coerce_bool)
        )

        # Normalize country_code to ISO alpha-2 (user CSVs may contain 3-letter codes)
        if 'country_code' in self.suppliers_df.columns:
            self.suppliers_df['country_code'] = (
                self.suppliers_df['country_code']
                .astype(str)
                .str.strip()
                .str.upper()
                .map(lambda c: self._normalize_country_code(c))
            )

        # Normalize numeric columns
        if 'contract_value_eur_m' in self.suppliers_df.columns:
            self.suppliers_df['contract_value_eur_m'] = (
                pd.to_numeric(self.suppliers_df['contract_value_eur_m'], errors='coerce')
                .fillna(0.0)
                .astype(float)
            )
        for int_col in ('financial_health', 'lead_time_days', 'past_disruptions'):
            if int_col in self.suppliers_df.columns:
                self.suppliers_df[int_col] = (
                    pd.to_numeric(self.suppliers_df[int_col], errors='coerce')
                    .fillna(0)
                    .astype(int)
                )

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
    
    @staticmethod
    def _coerce_bool(value) -> bool:
        """Convert various truthy/falsy representations to Python bool."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ('true', 'yes', '1')
        return False

    # ISO 3166-1 alpha-3 → alpha-2 mapping (covers all 195+ sovereign states)
    _ISO3_TO_ISO2: Dict[str, str] = {
        "AFG": "AF", "ALB": "AL", "DZA": "DZ", "AND": "AD", "AGO": "AO",
        "ATG": "AG", "ARG": "AR", "ARM": "AM", "AUS": "AU", "AUT": "AT",
        "AZE": "AZ", "BHS": "BS", "BHR": "BH", "BGD": "BD", "BRB": "BB",
        "BLR": "BY", "BEL": "BE", "BLZ": "BZ", "BEN": "BJ", "BTN": "BT",
        "BOL": "BO", "BIH": "BA", "BWA": "BW", "BRA": "BR", "BRN": "BN",
        "BGR": "BG", "BFA": "BF", "BDI": "BI", "CPV": "CV", "KHM": "KH",
        "CMR": "CM", "CAN": "CA", "CAF": "CF", "TCD": "TD", "CHL": "CL",
        "CHN": "CN", "COL": "CO", "COM": "KM", "COG": "CG", "COD": "CD",
        "CRI": "CR", "CIV": "CI", "HRV": "HR", "CUB": "CU", "CYP": "CY",
        "CZE": "CZ", "DNK": "DK", "DJI": "DJ", "DMA": "DM", "DOM": "DO",
        "ECU": "EC", "EGY": "EG", "SLV": "SV", "GNQ": "GQ", "ERI": "ER",
        "EST": "EE", "SWZ": "SZ", "ETH": "ET", "FJI": "FJ", "FIN": "FI",
        "FRA": "FR", "GAB": "GA", "GMB": "GM", "GEO": "GE", "DEU": "DE",
        "GHA": "GH", "GRC": "GR", "GRD": "GD", "GTM": "GT", "GIN": "GN",
        "GNB": "GW", "GUY": "GY", "HTI": "HT", "HND": "HN", "HUN": "HU",
        "ISL": "IS", "IND": "IN", "IDN": "ID", "IRN": "IR", "IRQ": "IQ",
        "IRL": "IE", "ISR": "IL", "ITA": "IT", "JAM": "JM", "JPN": "JP",
        "JOR": "JO", "KAZ": "KZ", "KEN": "KE", "KIR": "KI", "PRK": "KP",
        "KOR": "KR", "KWT": "KW", "KGZ": "KG", "LAO": "LA", "LVA": "LV",
        "LBN": "LB", "LSO": "LS", "LBR": "LR", "LBY": "LY", "LIE": "LI",
        "LTU": "LT", "LUX": "LU", "MDG": "MG", "MWI": "MW", "MYS": "MY",
        "MDV": "MV", "MLI": "ML", "MLT": "MT", "MHL": "MH", "MRT": "MR",
        "MUS": "MU", "MEX": "MX", "FSM": "FM", "MDA": "MD", "MCO": "MC",
        "MNG": "MN", "MNE": "ME", "MAR": "MA", "MOZ": "MZ", "MMR": "MM",
        "NAM": "NA", "NRU": "NR", "NPL": "NP", "NLD": "NL", "NZL": "NZ",
        "NIC": "NI", "NER": "NE", "NGA": "NG", "MKD": "MK", "NOR": "NO",
        "OMN": "OM", "PAK": "PK", "PLW": "PW", "PAN": "PA", "PNG": "PG",
        "PRY": "PY", "PER": "PE", "PHL": "PH", "POL": "PL", "PRT": "PT",
        "QAT": "QA", "ROU": "RO", "RUS": "RU", "RWA": "RW", "KNA": "KN",
        "LCA": "LC", "VCT": "VC", "WSM": "WS", "SMR": "SM", "STP": "ST",
        "SAU": "SA", "SEN": "SN", "SRB": "RS", "SYC": "SC", "SLE": "SL",
        "SGP": "SG", "SVK": "SK", "SVN": "SI", "SLB": "SB", "SOM": "SO",
        "ZAF": "ZA", "SSD": "SS", "ESP": "ES", "LKA": "LK", "SDN": "SD",
        "SUR": "SR", "SWE": "SE", "CHE": "CH", "SYR": "SY", "TWN": "TW",
        "TJK": "TJ", "TZA": "TZ", "THA": "TH", "TLS": "TL", "TGO": "TG",
        "TON": "TO", "TTO": "TT", "TUN": "TN", "TUR": "TR", "TKM": "TM",
        "TUV": "TV", "UGA": "UG", "UKR": "UA", "ARE": "AE", "GBR": "GB",
        "USA": "US", "URY": "UY", "UZB": "UZ", "VUT": "VU", "VEN": "VE",
        "VNM": "VN", "YEM": "YE", "ZMB": "ZM", "ZWE": "ZW",
        # Territories / common extras
        "HKG": "HK", "MAC": "MO", "PSE": "PS", "XKX": "XK", "SXM": "SX",
        "CUW": "CW", "ABW": "AW", "PRI": "PR", "GUM": "GU", "ASM": "AS",
    }

    @classmethod
    def _normalize_country_code(cls, code: str) -> str:
        """Normalize a country code to ISO alpha-2.

        If the code is already 2 letters, return it as-is (uppercase).
        If it's a 3-letter ISO code, convert to alpha-2 via lookup.
        Otherwise return the original value unchanged.
        """
        if len(code) == 2:
            return code
        if len(code) == 3:
            return cls._ISO3_TO_ISO2.get(code, code)
        return code

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