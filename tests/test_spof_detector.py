"""
Unit tests for SPOF (Single Point of Failure) Detector module.
"""

import pytest
import networkx as nx
from src.risk.spof_detector import SPOFDetector


@pytest.fixture
def spof_test_graph():
    """Create a test graph with known SPOFs."""
    G = nx.DiGraph()
    
    # SPOF case 1: High risk (>60) + no backup
    G.add_node('SPOF_HIGH_RISK', 
               tier=2, 
               risk_composite=75.0,
               risk_propagated=75.0,
               has_backup=False,
               component='Test Component A',
               name='High Risk SPOF')
    
    # SPOF case 2: Critical supplier + no backup
    G.add_node('SPOF_CRITICAL',
               tier=1,
               risk_composite=65.0,
               risk_propagated=65.0,
               has_backup=False,
               component='Test Component B',
               name='Critical SPOF')
    
    # NOT SPOF: Has backup
    G.add_node('HAS_BACKUP',
               tier=2,
               risk_composite=70.0,
               risk_propagated=70.0,
               has_backup=True,
               component='Test Component C',
               name='Has Backup')
    
    # NOT SPOF: Low risk
    G.add_node('LOW_RISK',
               tier=3,
               risk_composite=30.0,
               risk_propagated=30.0,
               has_backup=False,
               component='Test Component D',
               name='Low Risk')
    
    return G


def test_spof_detector_initialization(spof_test_graph):
    """Test SPOFDetector initializes correctly."""
    detector = SPOFDetector(spof_test_graph)
    assert detector.graph == spof_test_graph


def test_detect_all_spofs(spof_test_graph):
    """Test detecting all SPOFs in graph."""
    detector = SPOFDetector(spof_test_graph)
    spofs = detector.detect_all_spofs()
    
    # Should detect at least the 2 high-risk SPOFs
    assert len(spofs) >= 2
    assert 'SPOF_HIGH_RISK' in spofs
    assert 'SPOF_CRITICAL' in spofs
    
    # Has backup should NOT be SPOF
    assert 'HAS_BACKUP' not in spofs


def test_spof_flags_added_to_graph(spof_test_graph):
    """Test that SPOF flags are added to graph nodes."""
    detector = SPOFDetector(spof_test_graph)
    detector.detect_all_spofs()
    
    # Check all nodes have is_spof flag
    for node_id in spof_test_graph.nodes():
        assert 'is_spof' in spof_test_graph.nodes[node_id]
        assert isinstance(spof_test_graph.nodes[node_id]['is_spof'], bool)


def test_empty_graph():
    """Test SPOF detection on empty graph."""
    G = nx.DiGraph()
    detector = SPOFDetector(G)
    spofs = detector.detect_all_spofs()
    assert len(spofs) == 0


def test_spof_high_risk_detection():
    """Test that high risk suppliers are detected as SPOFs."""
    G = nx.DiGraph()
    
    G.add_node('HIGH_RISK',
               tier=2,
               risk_composite=75.0,
               risk_propagated=75.0,
               has_backup=False,
               component='Test Component',
               name='High Risk Supplier')
    
    detector = SPOFDetector(G)
    spofs = detector.detect_all_spofs()
    
    # High risk (>60) without backup should be SPOF
    assert 'HIGH_RISK' in spofs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])