"""
Unit tests for Risk Propagation module.
"""

import pytest
import networkx as nx
from src.risk.propagation import RiskPropagator


@pytest.fixture
def test_graph_with_risks():
    """Create a test graph with risk scores already calculated."""
    G = nx.DiGraph()
    
    # Tier-3 nodes (no children)
    G.add_node('T3_A', tier=3, risk_composite=80.0, name='Tier3 A')
    G.add_node('T3_B', tier=3, risk_composite=40.0, name='Tier3 B')
    
    # Tier-2 nodes (children from Tier-3)
    G.add_node('T2_A', tier=2, risk_composite=50.0, name='Tier2 A')
    G.add_node('T2_B', tier=2, risk_composite=30.0, name='Tier2 B')
    
    # Tier-1 nodes (children from Tier-2)
    G.add_node('T1_A', tier=1, risk_composite=20.0, name='Tier1 A')
    
    # Create dependency chain: T3 -> T2 -> T1
    G.add_edge('T3_A', 'T2_A')  # High-risk T3 feeds T2_A
    G.add_edge('T3_B', 'T2_A')  # Low-risk T3 also feeds T2_A
    G.add_edge('T3_B', 'T2_B')  # Low-risk T3 feeds T2_B
    G.add_edge('T2_A', 'T1_A')  # T2_A feeds T1_A
    G.add_edge('T2_B', 'T1_A')  # T2_B feeds T1_A
    
    return G


def test_propagator_initialization(test_graph_with_risks):
    """Test RiskPropagator initializes correctly."""
    propagator = RiskPropagator(test_graph_with_risks)
    
    assert propagator.graph == test_graph_with_risks
    assert propagator.graph.number_of_nodes() == 5


def test_tier3_propagation(test_graph_with_risks):
    """Test that Tier-3 nodes keep their composite risk."""
    propagator = RiskPropagator(test_graph_with_risks)
    propagated = propagator.propagate_all_risks()
    
    # Tier-3 should have propagated = composite
    assert propagated['T3_A'] == 80.0
    assert propagated['T3_B'] == 40.0


def test_tier2_propagation_increases_risk(test_graph_with_risks):
    """Test that Tier-2 risk increases when fed by high-risk Tier-3."""
    propagator = RiskPropagator(test_graph_with_risks)
    propagated = propagator.propagate_all_risks()
    
    # T2_A fed by T3_A (80) and T3_B (40) -> avg child = 60
    # own_risk * 0.6 + child_risk * 0.4 = 50 * 0.6 + 60 * 0.4 = 30 + 24 = 54
    # max(50, 54) = 54
    assert propagated['T2_A'] > test_graph_with_risks.nodes['T2_A']['risk_composite']
    assert propagated['T2_A'] >= 54.0


def test_tier2_propagation_no_decrease(test_graph_with_risks):
    """Test that propagation never decreases risk (uses max())."""
    propagator = RiskPropagator(test_graph_with_risks)
    propagated = propagator.propagate_all_risks()
    
    # T2_B fed only by T3_B (40), own risk is 30
    # Should not decrease below own risk
    assert propagated['T2_B'] >= test_graph_with_risks.nodes['T2_B']['risk_composite']


def test_tier1_cascading_propagation(test_graph_with_risks):
    """Test that Tier-1 receives cascaded risk from Tier-2 and Tier-3."""
    propagator = RiskPropagator(test_graph_with_risks)
    propagated = propagator.propagate_all_risks()
    
    # T1_A fed by T2_A and T2_B, both of which have propagated risk
    # Should be higher than its own composite risk (20)
    assert propagated['T1_A'] > test_graph_with_risks.nodes['T1_A']['risk_composite']


def test_propagation_added_to_graph(test_graph_with_risks):
    """Test that propagated risks are added to graph nodes."""
    propagator = RiskPropagator(test_graph_with_risks)
    propagator.propagate_all_risks()
    
    # Check all nodes have propagated risk
    for node_id in test_graph_with_risks.nodes():
        assert 'risk_propagated' in test_graph_with_risks.nodes[node_id]
        prop_risk = test_graph_with_risks.nodes[node_id]['risk_propagated']
        assert 0 <= prop_risk <= 100


def test_isolated_node_propagation():
    """Test propagation works with isolated nodes (no edges)."""
    G = nx.DiGraph()
    G.add_node('ISOLATED', tier=2, risk_composite=45.0, name='Isolated')
    
    propagator = RiskPropagator(G)
    propagated = propagator.propagate_all_risks()
    
    # Isolated node should keep its composite risk
    assert propagated['ISOLATED'] == 45.0


def test_diamond_topology_propagation():
    """Test that diamond topology (shared dependency) is handled correctly."""
    G = nx.DiGraph()
    
    # Create diamond: T3 -> T2_A, T2_B -> T1
    G.add_node('T3', tier=3, risk_composite=70.0, name='Tier3')
    G.add_node('T2_A', tier=2, risk_composite=40.0, name='Tier2 A')
    G.add_node('T2_B', tier=2, risk_composite=30.0, name='Tier2 B')
    G.add_node('T1', tier=1, risk_composite=20.0, name='Tier1')
    
    G.add_edge('T3', 'T2_A')
    G.add_edge('T3', 'T2_B')
    G.add_edge('T2_A', 'T1')
    G.add_edge('T2_B', 'T1')
    
    propagator = RiskPropagator(G)
    propagated = propagator.propagate_all_risks()
    
    # Both T2_A and T2_B should have increased risk from T3
    assert propagated['T2_A'] > 40.0
    assert propagated['T2_B'] > 30.0
    
    # T1 should have risk from both T2 nodes
    assert propagated['T1'] > 20.0


def test_propagation_statistics():
    """Test that propagation statistics are calculated correctly."""
    G = nx.DiGraph()
    
    # Create chain with clear propagation
    G.add_node('T3', tier=3, risk_composite=80.0, name='High Risk T3')
    G.add_node('T2', tier=2, risk_composite=20.0, name='Low Risk T2')
    G.add_node('T1', tier=1, risk_composite=15.0, name='Low Risk T1')
    
    G.add_edge('T3', 'T2')
    G.add_edge('T2', 'T1')
    
    propagator = RiskPropagator(G)
    propagated = propagator.propagate_all_risks()
    
    # T2 and T1 should have increased risk
    assert propagated['T2'] > 20.0
    assert propagated['T1'] > 15.0
    
    # T3 should stay the same
    assert propagated['T3'] == 80.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])