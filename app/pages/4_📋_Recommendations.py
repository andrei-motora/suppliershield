"""
Recommendations Page - Actionable risk mitigation recommendations.
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
from src.recommendations.engine import RecommendationEngine

st.set_page_config(page_title="Recommendations", page_icon="📋", layout="wide")

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
def generate_recommendations(_graph, _product_bom):
    """Generate recommendations."""
    engine = RecommendationEngine(
        graph=_graph,
        product_bom_df=_product_bom
    )
    
    recs = engine.generate_all_recommendations()
    regional_recs = engine.generate_regional_recommendations()
    summary = engine.generate_executive_summary(recs)
    
    return recs, regional_recs, summary


def main():
    st.title("📋 Recommendations")
    st.markdown("### Actionable Risk Mitigation Plan")
    st.markdown("---")
    
    # Load data
    with st.spinner("Generating recommendations..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks = calculate_risks(graph)
        recommendations, regional_recs, summary = generate_recommendations(
            graph, product_bom
        )
    
    st.success("✅ Recommendations generated!")
    
    # Executive Summary
    st.markdown("### 📊 Executive Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Actions",
            summary['total_recommendations']
        )
    
    with col2:
        st.metric(
            "🔴 Critical",
            summary['critical_count'],
            help="0-30 days"
        )
    
    with col3:
        st.metric(
            "🟠 High Priority",
            summary['high_count'],
            help="30-60 days"
        )
    
    with col4:
        st.metric(
            "🟡 Medium Priority",
            summary['medium_count'],
            help="60-90 days"
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "⚪ Watch Items",
            summary['watch_count'],
            help="Ongoing monitoring"
        )
    
    with col2:
        st.metric(
            "Suppliers Affected",
            summary['unique_suppliers']
        )
    
    with col3:
        st.metric(
            "Countries Affected",
            summary['unique_countries']
        )
    
    # Contract value at risk
    st.markdown("---")
    st.markdown("### 💰 Contract Value at Risk")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Critical Priority",
            f"€{summary['critical_contract_value']:.2f}M"
        )
    
    with col2:
        st.metric(
            "High Priority",
            f"€{summary['high_contract_value']:.2f}M"
        )
    
    # Priority filter
    st.markdown("---")
    st.markdown("### 🎯 Recommendations by Priority")
    
    priority_filter = st.selectbox(
        "Filter by Priority",
        ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']
    )
    
    # Filter recommendations
    if priority_filter == 'All':
        filtered_recs = recommendations
    else:
        filtered_recs = [r for r in recommendations if r['severity'] == priority_filter]
    
    st.markdown(f"**Showing {len(filtered_recs)} recommendations**")
    
    # Display recommendations by severity
    severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']
    severity_colors = {
        'CRITICAL': '#ef4444',
        'HIGH': '#f97316',
        'MEDIUM': '#eab308',
        'WATCH': '#94a3b8'
    }
    severity_emojis = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'WATCH': '⚪'
    }
    
    for severity in severity_order:
        severity_recs = [r for r in filtered_recs if r['severity'] == severity]
        
        if not severity_recs:
            continue
        
        st.markdown(f"### {severity_emojis[severity]} {severity} Priority ({severity_recs[0]['timeline']})")
        st.markdown(f"*{len(severity_recs)} actions*")
        
        for i, rec in enumerate(severity_recs, 1):
            with st.expander(
                f"{i}. {rec['supplier_id']} - {rec['supplier_name']} | {rec['action'][:50]}..."
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Supplier:** {rec['supplier_name']} ({rec['supplier_id']})")
                    st.markdown(f"**Component:** {rec['component']}")
                    st.markdown(f"**Country:** {rec['country']} | **Tier:** {rec['tier']}")
                    st.markdown(f"**Action:** {rec['action']}")
                    st.markdown(f"**Reason:** {rec['reason']}")
                    st.markdown(f"**Timeline:** {rec['timeline']}")
                
                with col2:
                    st.markdown("**Risk Metrics:**")
                    st.markdown(f"- Risk Score: {rec['propagated_risk']:.1f}")
                    st.markdown(f"- Contract: €{rec['contract_value']:.2f}M")
                    st.markdown(f"- Impact: {rec['impact_score']:.2f}")
                    
                    # Color-coded risk badge
                    if rec['propagated_risk'] >= 75:
                        st.error("🔴 CRITICAL RISK")
                    elif rec['propagated_risk'] >= 55:
                        st.warning("🟠 HIGH RISK")
                    elif rec['propagated_risk'] >= 35:
                        st.info("🟡 MEDIUM RISK")
                    else:
                        st.success("🟢 LOW RISK")
        
        st.markdown("---")
    
    # Regional recommendations
    if regional_recs:
        st.markdown("### 🌍 Regional Concentration Risks")
        
        for i, rec in enumerate(regional_recs, 1):
            with st.expander(
                f"{i}. {rec['region']} - {rec['concentration']:.1f}% concentration"
            ):
                st.markdown(f"**Region:** {rec['region']}")
                st.markdown(f"**Concentration:** {rec['concentration']:.1f}% of Tier-1/2 suppliers")
                st.markdown(f"**Supplier Count:** {rec['supplier_count']}")
                st.markdown(f"**Action:** {rec['action']}")
                st.markdown(f"**Reason:** {rec['reason']}")
                st.markdown(f"**Timeline:** {rec['timeline']}")
    
    # Download recommendations
    st.markdown("---")
    st.markdown("### 📥 Export Recommendations")
    
    # Convert to DataFrame
    df_recs = pd.DataFrame(recommendations)
    
    if not df_recs.empty:
        display_cols = [
            'severity', 'supplier_id', 'supplier_name', 'tier', 'country',
            'component', 'action', 'reason', 'timeline', 
            'propagated_risk', 'contract_value'
        ]
        
        df_export = df_recs[display_cols].copy()
        df_export.columns = [
            'Priority', 'Supplier ID', 'Supplier Name', 'Tier', 'Country',
            'Component', 'Action', 'Reason', 'Timeline',
            'Risk Score', 'Contract Value (€M)'
        ]
        
        csv = df_export.to_csv(index=False)
        
        st.download_button(
            label="📥 Download All Recommendations as CSV",
            data=csv,
            file_name="supplier_risk_recommendations.csv",
            mime="text/csv"
        )
    
    # Action plan summary
    st.markdown("---")
    st.markdown("### 📅 Implementation Timeline")
    
    st.info("""
    **Immediate (0-30 days):**
    - {} CRITICAL priority actions
    - Focus on suppliers with risk ≥ 75 and no backup
    - Establish emergency procurement protocols
    
    **Short-term (30-60 days):**
    - {} HIGH priority actions
    - Qualify backup suppliers for critical components
    - Establish dual-sourcing agreements
    
    **Medium-term (60-90 days):**
    - {} MEDIUM priority actions
    - Diversify away from concentrated regions
    - Review and update supplier risk assessments
    
    **Ongoing:**
    - {} WATCH items for continuous monitoring
    - Monitor supplier financial health
    - Quarterly risk assessment reviews
    """.format(
        summary['critical_count'],
        summary['high_count'],
        summary['medium_count'],
        summary['watch_count']
    ))
    
    # Next steps
    st.markdown("---")
    st.markdown("### 🚀 Next Steps")
    
    st.success("""
    **Recommended Actions:**
    
    1. **Present to S&OP Team** - Share this analysis in next planning meeting
    2. **Budget Allocation** - Request €{:.2f}M for backup qualification programs
    3. **Procurement Review** - Schedule sessions with top {} critical suppliers
    4. **Risk Monitoring** - Set up quarterly review process for top {} suppliers
    5. **Regional Diversification** - Evaluate sourcing alternatives in concentrated regions
    """.format(
        summary['high_contract_value'],
        min(20, summary['high_count']),
        min(50, summary['total_recommendations'])
    ))


if __name__ == "__main__":
    main()