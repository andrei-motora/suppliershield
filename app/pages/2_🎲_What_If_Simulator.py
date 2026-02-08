"""
What-If Simulator Page - Run Monte Carlo disruption scenarios.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer
from src.risk.propagation import RiskPropagator
from src.simulation.monte_carlo import MonteCarloSimulator

st.set_page_config(page_title="What-If Simulator", page_icon="🎲", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main {background-color: #0a0e1a;}
    h1, h2, h3 {color: #e2e8f0;}
    p, li, label {color: #8892a8;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache all data."""
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    return suppliers, dependencies, country_risk, product_bom


@st.cache_resource
def build_network(_suppliers, _dependencies, _country_risk):
    """Build and cache the network graph."""
    builder = SupplierNetworkBuilder()
    builder.load_data(_suppliers, _dependencies, _country_risk)
    graph = builder.build_graph()
    return graph


@st.cache_resource
def calculate_risks(_graph):
    """Calculate and cache risk scores."""
    scorer = RiskScorer(_graph)
    risk_scores = scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    
    propagator = RiskPropagator(_graph)
    propagated_risks = propagator.propagate_all_risks()
    
    return risk_scores, propagated_risks


def main():
    st.title("🎲 What-If Simulator")
    st.markdown("### Run Monte Carlo Disruption Scenarios")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks = calculate_risks(graph)
    
    # Initialize simulator
    simulator = MonteCarloSimulator(
        graph=graph,
        product_bom_df=product_bom,
        seed=42
    )
    
    # Scenario configuration
    st.markdown("### Configure Scenario")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Scenario type
        scenario_type = st.selectbox(
            "Scenario Type",
            ['single_node', 'regional'],
            format_func=lambda x: {
                'single_node': 'Single Supplier Failure',
                'regional': 'Regional Disruption'
            }[x]
        )
        
        # Target selection
        if scenario_type == 'single_node':
            # Get all suppliers
            supplier_options = sorted([
                f"{node} - {graph.nodes[node]['name']}"
                for node in graph.nodes()
            ])
            
            selected_supplier = st.selectbox(
                "Select Supplier",
                supplier_options
            )
            
            target = selected_supplier.split(' - ')[0]
            
        else:  # regional
            regions = sorted(set(
                graph.nodes[node]['region']
                for node in graph.nodes()
            ))
            
            selected_region = st.selectbox("Select Region", regions)
            
            # Get a representative supplier from region
            target = next(
                node for node in graph.nodes()
                if graph.nodes[node]['region'] == selected_region
            )
    
    with col2:
        # Duration
        duration = st.slider(
            "Disruption Duration (days)",
            min_value=7,
            max_value=90,
            value=30,
            step=7
        )
        
        # Iterations
        iterations = st.select_slider(
            "Simulation Iterations",
            options=[1000, 2000, 3000, 5000, 10000],
            value=3000
        )
    
    st.markdown("---")
    
    # Run simulation button
    if st.button("🚀 Run Simulation", type="primary"):
        
        with st.spinner(f"Running {iterations:,} Monte Carlo iterations..."):
            
            results = simulator.run_simulation(
                target_supplier=target,
                duration_days=duration,
                iterations=iterations,
                scenario_type=scenario_type
            )
        
        st.success("✅ Simulation complete!")
        
        # Display results
        st.markdown("---")
        st.markdown("### 📊 Simulation Results")
        
        # KPI cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Mean Impact",
                f"€{results['mean']:.2f}M",
                help="Expected revenue loss"
            )
        
        with col2:
            st.metric(
                "Median (P50)",
                f"€{results['median']:.2f}M",
                help="50th percentile impact"
            )
        
        with col3:
            st.metric(
                "95th Percentile",
                f"€{results['p95']:.2f}M",
                delta=f"+{results['p95'] - results['mean']:.2f}M",
                help="Bad scenario (1 in 20 chance)"
            )
        
        with col4:
            st.metric(
                "Worst Case",
                f"€{results['max']:.2f}M",
                delta=f"+{results['max'] - results['mean']:.2f}M",
                help="Maximum impact observed"
            )
        
        # Distribution histogram
        st.markdown("---")
        st.markdown("### Impact Distribution")
        
        hist_data = simulator.get_histogram_data(results['all_results'], bins=30)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=hist_data['bin_centers'],
            y=hist_data['counts'],
            marker_color='#f97316',
            name='Frequency'
        ))
        
        # Add vertical lines for statistics
        fig.add_vline(
            x=results['mean'],
            line_dash="dash",
            line_color="#22c55e",
            annotation_text=f"Mean: €{results['mean']:.2f}M",
            annotation_position="top"
        )
        
        fig.add_vline(
            x=results['p95'],
            line_dash="dash",
            line_color="#ef4444",
            annotation_text=f"P95: €{results['p95']:.2f}M",
            annotation_position="top"
        )
        
        fig.update_layout(
            title="Revenue Impact Distribution",
            xaxis_title="Revenue Impact (€M)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics table
        st.markdown("---")
        st.markdown("### Detailed Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Central Tendency:**")
            st.markdown(f"- Mean: €{results['mean']:.2f}M")
            st.markdown(f"- Median: €{results['median']:.2f}M")
            st.markdown(f"- Standard Deviation: €{results['std']:.2f}M")
        
        with col2:
            st.markdown("**Risk Percentiles:**")
            st.markdown(f"- P90: €{results['p90']:.2f}M")
            st.markdown(f"- P95: €{results['p95']:.2f}M")
            st.markdown(f"- P99: €{results['p99']:.2f}M")
            st.markdown(f"- Max: €{results['max']:.2f}M")
        
        # Interpretation
        st.markdown("---")
        st.markdown("### 💡 Interpretation for Management")
        
        st.info(f"""
        **What these numbers mean:**
        
        - **Mean Impact (€{results['mean']:.2f}M)**: This is the expected revenue loss in a typical disruption scenario. Budget this amount as contingency.
        
        - **95th Percentile (€{results['p95']:.2f}M)**: In a "bad luck" scenario (1 in 20 chance), losses could reach this level. Use this for risk planning.
        
        - **Worst Case (€{results['max']:.2f}M)**: Maximum observed impact across {iterations:,} simulations. While unlikely, this represents the upper bound.
        
        **Recommended Actions:**
        - Set aside €{results['p95']:.2f}M in contingency reserves
        - {"Qualify backup supplier immediately" if results['mean'] > 10 else "Monitor supplier closely"}
        - Review quarterly if mean impact > €5M
        """)
        
        # Scenario details
        st.markdown("---")
        st.markdown("### Scenario Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Target:** {target}")
            if scenario_type == 'single_node':
                st.markdown(f"**Supplier Name:** {graph.nodes[target]['name']}")
            st.markdown(f"**Scenario Type:** {scenario_type}")
        
        with col2:
            st.markdown(f"**Duration:** {duration} days")
            st.markdown(f"**Iterations:** {iterations:,}")
            st.markdown(f"**Affected Suppliers:** {results['affected_suppliers_count']}")


if __name__ == "__main__":
    main()