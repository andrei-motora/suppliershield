"""
Risk Rankings Page - View and filter all suppliers by risk.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer
from src.risk.propagation import RiskPropagator
from src.risk.spof_detector import SPOFDetector

st.set_page_config(page_title="Risk Rankings", page_icon="📊", layout="wide")

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
    
    spof_detector = SPOFDetector(_graph)
    spofs = spof_detector.detect_all_spofs()
    
    return risk_scores, propagated_risks, spofs


def get_risk_color(risk_score):
    """Get color based on risk score."""
    if risk_score >= 75:
        return "#ef4444"  # Critical - Red
    elif risk_score >= 55:
        return "#f97316"  # High - Orange
    elif risk_score >= 35:
        return "#eab308"  # Medium - Yellow
    else:
        return "#22c55e"  # Low - Green


def main():
    st.title("📊 Risk Rankings")
    st.markdown("### View and Filter All Suppliers")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks, spofs = calculate_risks(graph)
    
    # Build DataFrame
    data = []
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        data.append({
            'Supplier ID': node_id,
            'Name': node_data['name'],
            'Tier': node_data['tier'],
            'Country': node_data['country'],
            'Component': node_data['component'],
            'Composite Risk': node_data['risk_composite'],
            'Propagated Risk': node_data.get('risk_propagated', node_data['risk_composite']),
            'Category': node_data.get('risk_category', 'UNKNOWN'),
            'Contract Value (€M)': node_data['contract_value_eur_m'],
            'SPOF': 'Yes' if node_data.get('is_spof', False) else 'No',
            'Has Backup': 'Yes' if node_data.get('has_backup', False) else 'No',
            'Financial Health': node_data.get('financial_health', 0)
        })
    
    df = pd.DataFrame(data)
    
    # Filters
    st.sidebar.markdown("### Filters")
    
    # Tier filter
    tier_options = ['All'] + sorted(df['Tier'].unique().tolist())
    selected_tier = st.sidebar.selectbox("Tier", tier_options)
    
    # Risk category filter
    category_options = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    selected_category = st.sidebar.selectbox("Risk Category", category_options)
    
    # SPOF filter
    spof_options = ['All', 'Yes', 'No']
    selected_spof = st.sidebar.selectbox("SPOF Status", spof_options)
    
    # Country filter
    country_options = ['All'] + sorted(df['Country'].unique().tolist())
    selected_country = st.sidebar.selectbox("Country", country_options)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_tier != 'All':
        filtered_df = filtered_df[filtered_df['Tier'] == selected_tier]
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
    if selected_spof != 'All':
        filtered_df = filtered_df[filtered_df['SPOF'] == selected_spof]
    
    if selected_country != 'All':
        filtered_df = filtered_df[filtered_df['Country'] == selected_country]
    
    # Sort options
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sort By")
    
    sort_options = {
        'Propagated Risk (High to Low)': ('Propagated Risk', False),
        'Propagated Risk (Low to High)': ('Propagated Risk', True),
        'Composite Risk (High to Low)': ('Composite Risk', False),
        'Contract Value (High to Low)': ('Contract Value (€M)', False),
        'Supplier ID': ('Supplier ID', True)
    }
    
    selected_sort = st.sidebar.selectbox("Sort by", list(sort_options.keys()))
    sort_column, sort_ascending = sort_options[selected_sort]
    
    filtered_df = filtered_df.sort_values(sort_column, ascending=sort_ascending)
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df.index = filtered_df.index + 1
    
    # Display results
    st.markdown(f"### Results: {len(filtered_df)} suppliers")
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_risk = filtered_df['Propagated Risk'].mean()
        st.metric("Avg Propagated Risk", f"{avg_risk:.1f}")
    
    with col2:
        spof_count = (filtered_df['SPOF'] == 'Yes').sum()
        st.metric("SPOFs", spof_count)
    
    with col3:
        total_value = filtered_df['Contract Value (€M)'].sum()
        st.metric("Total Contract Value", f"€{total_value:.1f}M")
    
    with col4:
        critical_count = (filtered_df['Category'] == 'CRITICAL').sum()
        st.metric("Critical Risk", critical_count)
    
    st.markdown("---")
    
    # Display table
    # Format for display
    display_df = filtered_df.copy()
    display_df['Composite Risk'] = display_df['Composite Risk'].round(1)
    display_df['Propagated Risk'] = display_df['Propagated Risk'].round(1)
    display_df['Contract Value (€M)'] = display_df['Contract Value (€M)'].round(2)
    
    # Color code categories
    def highlight_category(row):
        if row['Category'] == 'CRITICAL':
            return ['background-color: rgba(239, 68, 68, 0.15)'] * len(row)
        elif row['Category'] == 'HIGH':
            return ['background-color: rgba(249, 115, 22, 0.15)'] * len(row)
        elif row['Category'] == 'MEDIUM':
            return ['background-color: rgba(234, 179, 8, 0.15)'] * len(row)
        else:
            return [''] * len(row)
    
    styled_df = display_df.style.apply(highlight_category, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=600
    )
    
    # Download button
    st.markdown("---")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="supplier_risk_rankings.csv",
        mime="text/csv"
    )
    
    # Top 10 Highest Risk
    st.markdown("---")
    st.markdown("### 🔴 Top 10 Highest Risk Suppliers")
    
    top_10 = filtered_df.nlargest(10, 'Propagated Risk')[
        ['Supplier ID', 'Name', 'Tier', 'Country', 'Propagated Risk', 'Category', 'SPOF']
    ]
    
    for idx, row in top_10.iterrows():
        with st.expander(f"{idx}. {row['Supplier ID']} - {row['Name']} (Risk: {row['Propagated Risk']:.1f})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Tier:** {row['Tier']}")
                st.markdown(f"**Country:** {row['Country']}")
                st.markdown(f"**Risk Category:** {row['Category']}")
            
            with col2:
                st.markdown(f"**Propagated Risk:** {row['Propagated Risk']:.1f}")
                st.markdown(f"**SPOF:** {row['SPOF']}")
                
                if row['SPOF'] == 'Yes':
                    st.error("⚠️ Single Point of Failure - Immediate action required!")


if __name__ == "__main__":
    main()