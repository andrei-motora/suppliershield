"""
Unit tests for Risk Scorer module.
"""

import pytest
import networkx as nx
import pandas as pd
from src.risk.scorer import RiskScorer


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    G = nx.DiGraph()
    
    # Add test nodes
    G.add_node('S001', 
               name='Test Supplier 1',
               tier=1,
               country='Germany',
               country_code='DE',
               region='Europe',
               component='Test Component',
               contract_value_eur_m=2.5,
               lead_time_days=30,
               financial_health=80,
               past_disruptions=1,
               has_backup=True,
               political_stability=15,
               natural_disaster_freq=20,
               logistics_performance=85,
               trade_restriction_risk=10)
    
    G.add_node('S002',
               name='Test Supplier 2',
               tier=2,
               country='China',
               country_code='CN',
               region='Asia-Pacific',
               component='Test Component 2',
               contract_value_eur_m=1.8,
               lead_time_days=45,
               financial_health=40,
               past_disruptions=3,
               has_backup=False,
               political_stability=55,
               natural_disaster_freq=45,
               logistics_performance=65,
               trade_restriction_risk=40)
    
    G.add_node('S003',
               name='Test Supplier 3',
               tier=3,
               country='DR Congo',
               country_code='CD',
               region='Africa',
               component='Test Component 3',
               contract_value_eur_m=0.5,
               lead_time_days=60,
               financial_health=20,
               past_disruptions=5,
               has_backup=False,
               political_stability=75,
               natural_disaster_freq=30,
               logistics_performance=40,
               trade_restriction_risk=65)
    
    return G


def test_risk_scorer_initialization(sample_graph):
    """Test RiskScorer initializes correctly."""
    scorer = RiskScorer(sample_graph)
    
    assert scorer.graph == sample_graph
    assert scorer.graph.number_of_nodes() == 3


def test_calculate_geopolitical_risk(sample_graph):
    """Test geopolitical risk calculation."""
    scorer = RiskScorer(sample_graph)
    
    # Low risk country (Germany)
    geo_risk_s001 = scorer._calculate_geopolitical_risk('S001')
    assert 0 <= geo_risk_s001 <= 100
    assert geo_risk_s001 < 30  # Germany should be low risk
    
    # High risk country (DR Congo)
    geo_risk_s003 = scorer._calculate_geopolitical_risk('S003')
    assert 0 <= geo_risk_s003 <= 100
    assert geo_risk_s003 > 60  # DR Congo should be high risk


def test_calculate_financial_risk(sample_graph):
    """Test financial risk calculation."""
    scorer = RiskScorer(sample_graph)
    
    # High financial health (80) -> Low risk
    fin_risk_s001 = scorer._calculate_financial_risk('S001')
    assert 0 <= fin_risk_s001 <= 100
    assert fin_risk_s001 < 30
    
    # Low financial health (20) -> High risk
    fin_risk_s003 = scorer._calculate_financial_risk('S003')
    assert 0 <= fin_risk_s003 <= 100
    assert fin_risk_s003 > 70


def test_calculate_logistics_risk(sample_graph):
    """Test logistics risk calculation."""
    scorer = RiskScorer(sample_graph)
    
    # Good logistics (85) -> Low risk
    log_risk_s001 = scorer._calculate_logistics_risk('S001')
    assert 0 <= log_risk_s001 <= 100
    assert log_risk_s001 < 30
    
    # Poor logistics (40) -> High risk
    log_risk_s003 = scorer._calculate_logistics_risk('S003')
    assert 0 <= log_risk_s003 <= 100
    assert log_risk_s003 > 50


def test_calculate_concentration_risk(sample_graph):
    """Test concentration risk calculation."""
    scorer = RiskScorer(sample_graph)
    
    # Add edges to create dependencies
    sample_graph.add_edge('S002', 'S001', dependency_weight=80)
    sample_graph.add_edge('S003', 'S002', dependency_weight=90)
    
    # Tier-1 with 1 incoming edge
    conc_risk_s001 = scorer._calculate_concentration_risk('S001')
    assert conc_risk_s001 == 75  # Tier-1 with <= 1 incoming
    
    # Calculate for node with no incoming edges
    conc_risk_s003 = scorer._calculate_concentration_risk('S003')
    assert conc_risk_s003 == 60  # Tier-2/3 with <= 1 incoming


def test_calculate_all_risks(sample_graph):
    """Test calculating risks for all nodes."""
    scorer = RiskScorer(sample_graph)
    
    risk_scores = scorer.calculate_all_risks()
    
    # Should have scores for all 3 nodes
    assert len(risk_scores) == 3
    
    # Check that all nodes have scores
    for node_id in sample_graph.nodes():
        assert node_id in risk_scores


def test_add_scores_to_graph(sample_graph):
    """Test adding risk scores to graph nodes."""
    scorer = RiskScorer(sample_graph)
    scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    # Check that scores were added to nodes
    for node_id in sample_graph.nodes():
        node_data = sample_graph.nodes[node_id]
        
        assert 'risk_composite' in node_data
        assert 'risk_category' in node_data
        assert 'risk_geopolitical' in node_data
        assert 'risk_financial' in node_data
        
        # Check values are valid
        assert 0 <= node_data['risk_composite'] <= 100
        assert node_data['risk_category'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']


def test_risk_scorer_with_no_edges(sample_graph):
    """Test risk scorer works with isolated nodes."""
    scorer = RiskScorer(sample_graph)
    
    # Calculate without any edges
    risk_scores = scorer.calculate_all_risks()
    
    # Should still calculate scores
    assert len(risk_scores) == 3


def test_risk_scores_in_valid_range(sample_graph):
    """Test that all risk scores are in valid 0-100 range."""
    scorer = RiskScorer(sample_graph)
    scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    for node_id in sample_graph.nodes():
        node_data = sample_graph.nodes[node_id]
        
        # Check composite risk
        assert 0 <= node_data['risk_composite'] <= 100
        
        # Check individual dimensions if they exist
        if 'risk_geopolitical' in node_data:
            assert 0 <= node_data['risk_geopolitical'] <= 100
        if 'risk_financial' in node_data:
            assert 0 <= node_data['risk_financial'] <= 100


def test_high_risk_supplier_has_higher_score(sample_graph):
    """Test that high-risk suppliers get higher scores than low-risk ones."""
    scorer = RiskScorer(sample_graph)
    scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    # S001 (Germany, high financial health) should have lower risk
    s001_risk = sample_graph.nodes['S001']['risk_composite']
    
    # S003 (DR Congo, low financial health) should have higher risk
    s003_risk = sample_graph.nodes['S003']['risk_composite']
    
    assert s003_risk > s001_risk


if __name__ == '__main__':
    pytest.main([__file__, '-v'])