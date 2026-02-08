"""
Sensitivity Analysis Page - Criticality ranking of suppliers.
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
from src.simulation.sensitivity import SensitivityAnalyzer

st.set_page_config(page_title="Sensitivity Analysis", page_icon="📈", layout="wide")

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


@st.cache_data
def get_criticality_ranking(_graph, _product_bom):
    """Calculate criticality ranking."""
    analyzer = SensitivityAnalyzer(
        graph=_graph,
        product_bom_df=_product_bom
    )
    
    ranking = analyzer.calculate_criticality_ranking()
    pareto = analyzer.get_pareto_analysis()
    tier_stats = analyzer.analyze_by_tier()
    country_stats = analyzer.analyze_by_country(top_n=10)
    
    return ranking, pareto, tier_stats, country_stats


def main():
    st.title("📈 Sensitivity Analysis")
    st.markdown("### Criticality Ranking: Which Suppliers Matter Most?")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data and calculating criticality..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks = calculate_risks(graph)
        ranking, pareto, tier_stats, country_stats = get_criticality_ranking(
            graph, product_bom
        )
    
    st.success("✅ Analysis complete!")
    
    # Pareto Analysis
    st.markdown("### 🎯 Pareto Analysis (80/20 Rule)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "50% of Risk",
            f"{pareto['pareto_50_suppliers']} suppliers",
            delta=f"{pareto['pareto_50_percent']:.1f}% of total"
        )
    
    with col2:
        st.metric(
            "80% of Risk",
            f"{pareto['pareto_80_suppliers']} suppliers",
            delta=f"{pareto['pareto_80_percent']:.1f}% of total"
        )
    
    with col3:
        st.metric(
            "Top 10 Share",
            f"{pareto['top_10_percent']:.1f}%",
            help="Percentage of total criticality from top 10 suppliers"
        )
    
    st.info(f"""
    **Key Insight:** Just **{pareto['pareto_50_suppliers']} suppliers ({pareto['pareto_50_percent']:.1f}%)** 
    account for **50% of total criticality**. Focus your risk mitigation efforts here first!
    """)
    
    # Top N selector
    st.markdown("---")
    st.markdown("### 🏆 Top Critical Suppliers")
    
    top_n = st.slider("Show top N suppliers", min_value=5, max_value=50, value=20, step=5)
    
    top_suppliers = ranking.head(top_n)
    
    # Criticality bar chart
    fig = go.Figure()
    
    # Color bars by risk category
    colors = []
    for _, row in top_suppliers.iterrows():
        if row['propagated_risk'] >= 75:
            colors.append('#ef4444')  # Critical
        elif row['propagated_risk'] >= 55:
            colors.append('#f97316')  # High
        elif row['propagated_risk'] >= 35:
            colors.append('#eab308')  # Medium
        else:
            colors.append('#22c55e')  # Low
    
    fig.add_trace(go.Bar(
        y=[f"{row['supplier_id']}" for _, row in top_suppliers.iterrows()],
        x=top_suppliers['criticality_score'],
        orientation='h',
        marker_color=colors,
        text=[f"{score:.1f}" for score in top_suppliers['criticality_score']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Criticality: %{x:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Most Critical Suppliers (Risk × Exposure)",
        xaxis_title="Criticality Score",
        yaxis_title="Supplier",
        template="plotly_dark",
        height=max(400, top_n * 20),
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.markdown("---")
    st.markdown(f"### 📋 Top {top_n} Suppliers - Detailed View")
    
    display_cols = [
        'supplier_id', 'name', 'tier', 'country', 'component',
        'criticality_score', 'propagated_risk', 'total_revenue_exposure',
        'affected_products', 'downstream_suppliers'
    ]
    
    display_df = top_suppliers[display_cols].copy()
    display_df.columns = [
        'ID', 'Name', 'Tier', 'Country', 'Component',
        'Criticality', 'Risk', 'Exposure (€M)',
        'Products', 'Downstream'
    ]
    
    display_df['Criticality'] = display_df['Criticality'].round(2)
    display_df['Risk'] = display_df['Risk'].round(1)
    display_df['Exposure (€M)'] = display_df['Exposure (€M)'].round(2)
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Top Suppliers as CSV",
        data=csv,
        file_name=f"top_{top_n}_critical_suppliers.csv",
        mime="text/csv"
    )
    
    # Analysis by Tier
    st.markdown("---")
    st.markdown("### 📊 Analysis by Tier")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(
            tier_stats.round(2),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # Tier comparison chart
        fig_tier = go.Figure()
        
        fig_tier.add_trace(go.Bar(
            x=tier_stats['Tier'],
            y=tier_stats['Avg Criticality'],
            marker_color='#f97316',
            name='Avg Criticality',
            text=[f"{val:.2f}" for val in tier_stats['Avg Criticality']],
            textposition='outside'
        ))
        
        fig_tier.update_layout(
            title="Average Criticality by Tier",
            xaxis_title="Tier",
            yaxis_title="Average Criticality",
            template="plotly_dark",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig_tier, use_container_width=True)
    
    highest_tier = tier_stats.loc[tier_stats['Avg Criticality'].idxmax(), 'Tier']
    st.info(f"**Insight:** Tier-{int(highest_tier)} has the highest average criticality. Focus mitigation efforts here!")
    
    # Analysis by Country
    st.markdown("---")
    st.markdown("### 🌍 Analysis by Country (Top 10)")
    
    st.dataframe(
        country_stats.round(2),
        use_container_width=True,
        height=400
    )
    
    # Country chart
    fig_country = go.Figure()
    
    fig_country.add_trace(go.Bar(
        x=country_stats.index[:10],
        y=country_stats['Total Criticality'][:10],
        marker_color='#8b5cf6',
        text=[f"{val:.1f}" for val in country_stats['Total Criticality'][:10]],
        textposition='outside'
    ))
    
    fig_country.update_layout(
        title="Total Criticality by Country (Top 10)",
        xaxis_title="Country",
        yaxis_title="Total Criticality",
        template="plotly_dark",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig_country, use_container_width=True)
    
    top_countries = country_stats.index[:3].tolist()
    st.warning(f"**Concentration Risk:** Focus diversification efforts on: {', '.join(top_countries)}")
    
    # Explanation
    st.markdown("---")
    st.markdown("### 💡 Understanding Criticality")
    
    st.info("""
    **Criticality Score = Risk × Revenue Exposure**
    
    This metric combines two dimensions:
    1. **Risk Score** - How likely is this supplier to fail?
    2. **Revenue Exposure** - How much revenue is at stake if it fails?
    
    **Why it matters:**
    - A low-risk supplier with huge exposure can be more critical than a high-risk supplier with small exposure
    - Criticality helps you prioritize where to invest in risk mitigation
    - Focus on the top 20-30 suppliers first - they drive most of your risk
    
    **Action Priority:**
    1. Start with suppliers in the top 20
    2. Qualify backup suppliers for components with criticality > 15
    3. Monitor suppliers with criticality 10-15 quarterly
    4. Standard monitoring for criticality < 10
    """)


if __name__ == "__main__":
    main()