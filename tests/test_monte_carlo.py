"""
Unit tests for Monte Carlo Simulation module.
"""

import pytest
import networkx as nx
import pandas as pd
from src.simulation.monte_carlo import MonteCarloSimulator


@pytest.fixture
def monte_carlo_graph():
    """Create a test graph for Monte Carlo simulation."""
    G = nx.DiGraph()
    
    # Add suppliers with BOTH risk_composite and risk_propagated
    G.add_node('S001', tier=1, risk_composite=40.0, risk_propagated=40.0, name='Supplier 1')
    G.add_node('S002', tier=2, risk_composite=60.0, risk_propagated=60.0, name='Supplier 2')
    G.add_node('S003', tier=3, risk_composite=80.0, risk_propagated=80.0, name='Supplier 3')
    
    # Add dependencies
    G.add_edge('S003', 'S002')
    G.add_edge('S002', 'S001')
    
    return G


@pytest.fixture
def product_bom_data():
    """Create test product BOM data."""
    return pd.DataFrame({
        'product_id': ['P001', 'P002'],
        'product_name': ['Product A', 'Product B'],
        'annual_revenue_eur_m': [5.0, 3.0],
        'component_supplier_ids': ['S001', 'S001,S002']
    })


def test_simulator_initialization(monte_carlo_graph, product_bom_data):
    """Test MonteCarloSimulator initializes correctly."""
    simulator = MonteCarloSimulator(
        graph=monte_carlo_graph,
        product_bom_df=product_bom_data,
        seed=42
    )
    
    assert simulator.graph == monte_carlo_graph
    assert len(simulator.product_bom_df) == 2


def test_simulation_runs_successfully(monte_carlo_graph, product_bom_data):
    """Test that simulation runs without errors."""
    simulator = MonteCarloSimulator(
        graph=monte_carlo_graph,
        product_bom_df=product_bom_data,
        seed=42
    )
    
    result = simulator.run_simulation(
        target_supplier='S002',
        duration_days=30,
        iterations=100,
        scenario_type='single_node'
    )
    
    # Check result structure
    assert 'mean' in result
    assert 'median' in result
    assert 'p95' in result
    assert 'max' in result


def test_simulation_has_variance():
    """Test that simulation produces varied results (stochastic behavior)."""
    G = nx.DiGraph()
    G.add_node('S001', tier=1, risk_composite=60.0, risk_propagated=60.0, name='Test')
    
    bom = pd.DataFrame({
        'product_id': ['P001'],
        'product_name': ['Product'],
        'annual_revenue_eur_m': [5.0],
        'component_supplier_ids': ['S001']
    })
    
    simulator = MonteCarloSimulator(graph=G, product_bom_df=bom, seed=42)
    
    result = simulator.run_simulation(
        target_supplier='S001',
        duration_days=30,
        iterations=100,
        scenario_type='single_node'
    )
    
    # With randomness, we should have variance
    assert result['std'] > 0
    assert result['max'] > result['min']


def test_simulation_statistics_valid(monte_carlo_graph, product_bom_data):
    """Test that simulation statistics are valid."""
    simulator = MonteCarloSimulator(
        graph=monte_carlo_graph,
        product_bom_df=product_bom_data,
        seed=42
    )
    
    result = simulator.run_simulation(
        target_supplier='S002',
        duration_days=30,
        iterations=200,
        scenario_type='single_node'
    )
    
    # All values should be non-negative
    assert result['mean'] >= 0
    assert result['median'] >= 0
    assert result['p95'] >= result['median']
    assert result['max'] >= result['p95']


def test_histogram_data_generation(monte_carlo_graph, product_bom_data):
    """Test histogram data generation."""
    simulator = MonteCarloSimulator(
        graph=monte_carlo_graph,
        product_bom_df=product_bom_data,
        seed=42
    )
    
    result = simulator.run_simulation(
        target_supplier='S002',
        duration_days=30,
        iterations=100,
        scenario_type='single_node'
    )
    
    hist_data = simulator.get_histogram_data(result['all_results'], bins=10)
    
    assert 'counts' in hist_data
    assert 'bin_edges' in hist_data
    assert len(hist_data['counts']) == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])