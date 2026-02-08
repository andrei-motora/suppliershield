"""
SupplierShield - Streamlit Dashboard
Main entry point for the interactive dashboard.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer
from src.risk.propagation import RiskPropagator
from src.risk.spof_detector import SPOFDetector

# Page configuration
st.set_page_config(
    page_title="SupplierShield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and styling
st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #0a0e1a;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #0d1220;
    }
    
    /* Metric cards */
    .css-1xarl3l {
        background-color: #111827;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Headers */
    h1 {
        color: #e2e8f0;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #e2e8f0;
    }
    
    /* Text */
    p, li, label {
        color: #8892a8;
    }
    
    /* Dataframe */
    .dataframe {
        background-color: #111827;
        color: #e2e8f0;
    }
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
    
    spof_detector = SPOFDetector(_graph)
    spofs = spof_detector.detect_all_spofs()
    
    return risk_scores, propagated_risks, spofs


def main():
    """Main dashboard home page."""
    
    # Sidebar
    st.sidebar.title("🛡️ SupplierShield")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Multi-Tier Supplier Risk Analyzer**")
    st.sidebar.markdown("")
    
    st.sidebar.info("""
    Navigate using the pages in the sidebar:
    
    📊 **Risk Rankings** - View all suppliers
    
    🎲 **What-If Simulator** - Run scenarios
    
    📈 **Sensitivity Analysis** - Criticality ranking
    
    📋 **Recommendations** - Action plan
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("Built by **Andrei**")
    st.sidebar.markdown("HBO University Venlo")
    
    # Main content
    st.title("🛡️ SupplierShield Dashboard")
    st.markdown("### Multi-Tier Supplier Risk & Resilience Analyzer")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks, spofs = calculate_risks(graph)
    
    # Welcome message
    st.success("✅ Data loaded successfully!")
    
    # KPI Cards
    st.markdown("### Network Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Suppliers",
            value=graph.number_of_nodes(),
            delta=None
        )
    
    with col2:
        critical_count = sum(
            1 for node in graph.nodes()
            if graph.nodes[node].get('risk_category') == 'CRITICAL'
        )
        st.metric(
            label="🔴 Critical Risk",
            value=critical_count,
            delta=f"{critical_count/graph.number_of_nodes()*100:.1f}%"
        )
    
    with col3:
        st.metric(
            label="⚠️ SPOFs Detected",
            value=len(spofs),
            delta=f"{len(spofs)/graph.number_of_nodes()*100:.1f}%"
        )
    
    with col4:
        avg_risk = sum(
            graph.nodes[node].get('risk_propagated', 
                graph.nodes[node]['risk_composite'])
            for node in graph.nodes()
        ) / graph.number_of_nodes()
        
        st.metric(
            label="📊 Avg Risk Score",
            value=f"{avg_risk:.1f}",
            delta=None
        )
    
    st.markdown("---")
    
    # Risk Distribution
    st.markdown("### Risk Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**By Category:**")
        
        categories = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        for node in graph.nodes():
            cat = graph.nodes[node].get('risk_category', 'UNKNOWN')
            if cat in categories:
                categories[cat] += 1
        
        for cat, count in categories.items():
            percentage = count / graph.number_of_nodes() * 100
            
            if cat == 'CRITICAL':
                st.markdown(f"🔴 **{cat}**: {count} ({percentage:.1f}%)")
            elif cat == 'HIGH':
                st.markdown(f"🟠 **{cat}**: {count} ({percentage:.1f}%)")
            elif cat == 'MEDIUM':
                st.markdown(f"🟡 **{cat}**: {count} ({percentage:.1f}%)")
            else:
                st.markdown(f"🟢 **{cat}**: {count} ({percentage:.1f}%)")
    
    with col2:
        st.markdown("**By Tier:**")
        
        for tier in [1, 2, 3]:
            tier_nodes = [
                n for n in graph.nodes() 
                if graph.nodes[n]['tier'] == tier
            ]
            tier_avg_risk = sum(
                graph.nodes[n].get('risk_propagated', 
                    graph.nodes[n]['risk_composite'])
                for n in tier_nodes
            ) / len(tier_nodes)
            
            st.markdown(f"**Tier-{tier}**: {len(tier_nodes)} suppliers, avg risk {tier_avg_risk:.1f}")
    
    st.markdown("---")
    
    # Quick Stats
    st.markdown("### Network Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Graph Metrics:**")
        st.markdown(f"- Nodes: {graph.number_of_nodes()}")
        st.markdown(f"- Edges: {graph.number_of_edges()}")
        st.markdown(f"- Avg Degree: {graph.number_of_edges() / graph.number_of_nodes():.2f}")
    
    with col2:
        st.markdown("**Risk Propagation:**")
        
        increased_count = sum(
            1 for node in graph.nodes()
            if graph.nodes[node].get('risk_propagated', 0) > 
               graph.nodes[node]['risk_composite']
        )
        
        st.markdown(f"- Suppliers with increased risk: {increased_count}")
        st.markdown(f"- Percentage: {increased_count/graph.number_of_nodes()*100:.1f}%")
    
    with col3:
        st.markdown("**SPOFs:**")
        st.markdown(f"- Total SPOFs: {len(spofs)}")
        
        critical_spofs = sum(
            1 for spof_id in spofs
            if graph.nodes[spof_id].get('risk_propagated', 
                graph.nodes[spof_id]['risk_composite']) >= 60
        )
        st.markdown(f"- Critical SPOFs: {critical_spofs}")
    
    st.markdown("---")
    
    # Getting Started
    st.markdown("### 🚀 Getting Started")
    
    st.info("""
    **Explore the dashboard using the sidebar pages:**
    
    1. **📊 Risk Rankings** - View and filter all 120 suppliers by risk level, tier, and country
    
    2. **🎲 What-If Simulator** - Run Monte Carlo simulations to estimate revenue impact of supplier failures
    
    3. **📈 Sensitivity Analysis** - See which suppliers are most critical (Risk × Exposure)
    
    4. **📋 Recommendations** - Get prioritized action plan with timelines
    """)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #5a6478; padding: 2rem 0;'>
        <p>SupplierShield v1.0 | Built with Python, NetworkX, and Streamlit</p>
        <p>© 2026 Andrei | HBO University Venlo</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()