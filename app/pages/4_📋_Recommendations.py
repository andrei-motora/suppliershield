"""
Recommendations Page - Actionable risk mitigation recommendations.
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
from src.recommendations.engine import RecommendationEngine

# Add app directory so shared_styles can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_styles import (
    inject_css, COLORS, PLOTLY_LAYOUT_DEFAULTS,
    section_header, severity_badge,
)

st.set_page_config(page_title="Recommendations", page_icon="📋", layout="wide")
inject_css()


@st.cache_data
def load_data():
    data_dir = project_root / 'data' / 'raw'
    validator = DataValidator(data_dir)
    suppliers, dependencies, country_risk, product_bom = validator.load_all()
    return suppliers, dependencies, country_risk, product_bom


@st.cache_resource
def build_network(_suppliers, _dependencies, _country_risk):
    builder = SupplierNetworkBuilder()
    builder.load_data(_suppliers, _dependencies, _country_risk)
    return builder.build_graph()


@st.cache_resource
def calculate_risks(_graph):
    scorer = RiskScorer(_graph)
    risk_scores = scorer.calculate_all_risks()
    scorer.add_scores_to_graph()
    propagator = RiskPropagator(_graph)
    propagated_risks = propagator.propagate_all_risks()
    return risk_scores, propagated_risks


@st.cache_data
def generate_recommendations(_graph, _product_bom):
    engine = RecommendationEngine(graph=_graph, product_bom_df=_product_bom)
    recs = engine.generate_all_recommendations()
    regional_recs = engine.generate_regional_recommendations()
    summary = engine.generate_executive_summary(recs)
    return recs, regional_recs, summary


def _build_severity_donut(summary):
    """Donut chart of severity distribution."""
    labels = ['CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']
    values = [summary['critical_count'], summary['high_count'],
              summary['medium_count'], summary['watch_count']]
    colors_list = [COLORS['CRITICAL'], COLORS['HIGH'], COLORS['MEDIUM'], COLORS['text_muted']]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors_list, line=dict(color='rgba(10,14,26,0.8)', width=2)),
        textinfo='label+value',
        textfont=dict(size=12, family='Inter', color=COLORS['text_primary']),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>',
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{summary['total_recommendations']}</b><br><span style='font-size:11px;color:#94a3b8'>actions</span>",
        showarrow=False,
        font=dict(size=26, color=COLORS['text_primary'], family='JetBrains Mono'),
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=300,
        margin=dict(t=30, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5,
                    font=dict(size=11, color=COLORS['text_muted'])),
        title={'text': "Actions by Severity", 'font': {'size': 15, 'color': COLORS['text_secondary']}},
    )
    return fig


def main():
    st.title("📋 Recommendations")
    st.markdown("### Prioritized Risk Mitigation Action Plan")
    st.divider()

    # Load data
    with st.spinner("🔄 Generating recommendations..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks = calculate_risks(graph)
        recommendations, regional_recs, summary = generate_recommendations(graph, product_bom)

    st.success("✅ **Recommendation Engine Complete!** Generated prioritized action plan")

    # ── Executive Summary KPIs ──
    section_header("Executive Summary", icon="📊")

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📋 Total Actions", summary['total_recommendations'])
        with c2:
            st.metric("🔴 Critical", summary['critical_count'], delta="0-30 days", delta_color="inverse")
        with c3:
            st.metric("🟠 High Priority", summary['high_count'], delta="30-60 days")
        with c4:
            st.metric("🟡 Medium Priority", summary['medium_count'], delta="60-90 days")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("⚪ Watch Items", summary['watch_count'], delta="Ongoing")
        with c2:
            st.metric("👥 Suppliers Affected", summary['unique_suppliers'])
        with c3:
            st.metric("🌍 Countries Affected", summary['unique_countries'])

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # TABS: Action Items | Timeline | Summary Dashboard
    # ═══════════════════════════════════════════════════════════
    tab_actions, tab_timeline, tab_summary = st.tabs(["Action Items", "Timeline", "Summary Dashboard"])

    # ── TAB 1: Action Items ───────────────────────────────────
    with tab_actions:
        # Filter
        c1, c2 = st.columns([3, 1])
        with c1:
            priority_filter = st.selectbox("Filter by Priority Level",
                                            ['All Priorities', 'CRITICAL', 'HIGH', 'MEDIUM', 'WATCH'])
        with c2:
            if priority_filter == 'All Priorities':
                filtered_count = len(recommendations)
            else:
                filtered_count = sum(1 for r in recommendations if r['severity'] == priority_filter)
            st.metric("Showing", filtered_count)

        filtered_recs = (recommendations if priority_filter == 'All Priorities'
                         else [r for r in recommendations if r['severity'] == priority_filter])

        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']
        severity_configs = {
            'CRITICAL': {'emoji': '🔴', 'color': COLORS['CRITICAL'], 'timeline': '0-30 days',
                         'bg': f"rgba(239, 68, 68, 0.1)"},
            'HIGH':     {'emoji': '🟠', 'color': COLORS['HIGH'], 'timeline': '30-60 days',
                         'bg': f"rgba(249, 115, 22, 0.1)"},
            'MEDIUM':   {'emoji': '🟡', 'color': COLORS['MEDIUM'], 'timeline': '60-90 days',
                         'bg': f"rgba(234, 179, 8, 0.1)"},
            'WATCH':    {'emoji': '⚪', 'color': COLORS['text_muted'], 'timeline': 'Ongoing monitoring',
                         'bg': f"rgba(148, 163, 184, 0.1)"},
        }

        for sev in severity_order:
            sev_recs = [r for r in filtered_recs if r['severity'] == sev]
            if not sev_recs:
                continue

            cfg = severity_configs[sev]
            st.markdown(f"""
            <div style='background: {cfg['bg']}; border-left: 4px solid {cfg['color']};
                        padding: 1rem; border-radius: 8px; margin: 1.5rem 0;'>
                <h2 style='color: {cfg['color']}; margin: 0; font-size: 1.5rem;'>
                    {cfg['emoji']} {sev} PRIORITY
                </h2>
                <p style='color: #cbd5e0; margin: 0.5rem 0 0 0;'>
                    <strong>{len(sev_recs)} actions</strong> • Timeline: {cfg['timeline']}
                </p>
            </div>
            """, unsafe_allow_html=True)

            for i, rec in enumerate(sev_recs, 1):
                badge = severity_badge(rec['severity'])
                risk = rec['propagated_risk']
                if risk >= 75:
                    rc, rl = COLORS['CRITICAL'], 'CRITICAL RISK'
                elif risk >= 55:
                    rc, rl = COLORS['HIGH'], 'HIGH RISK'
                elif risk >= 35:
                    rc, rl = COLORS['MEDIUM'], 'MEDIUM RISK'
                else:
                    rc, rl = COLORS['LOW'], 'LOW RISK'

                with st.expander(f"#{i} • {rec['supplier_id']} - {rec['supplier_name']} • {rec['component']}"):
                    st.markdown(badge, unsafe_allow_html=True)

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown("### 📋 Supplier Information")
                        st.markdown(f"**Supplier:** {rec['supplier_name']} ({rec['supplier_id']})")
                        st.markdown(f"**Component:** {rec['component']}")
                        st.markdown(f"**Country:** {rec['country']} | **Tier:** {rec['tier']}")
                        st.divider()
                        st.markdown("### 🎯 Recommended Action")
                        st.markdown(f"**Action:** {rec['action']}")
                        st.markdown(f"**Reason:** {rec['reason']}")
                        st.markdown(f"**Timeline:** {rec['timeline']}")
                    with c2:
                        st.markdown("### 📊 Risk Metrics")
                        st.markdown(f"""
                        <div style='background: {rc}15; border: 2px solid {rc};
                                    padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                            <div style='color: {rc}; font-weight: 700; font-size: 1.1rem;
                                        font-family: "JetBrains Mono";'>
                                {rec['propagated_risk']:.1f}/100
                            </div>
                            <div style='color: {rc}; font-size: 0.85rem; margin-top: 0.25rem;'>{rl}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"**Contract Value:** €{rec['contract_value']:.2f}M")
                        st.markdown(f"**Impact Score:** {rec['impact_score']:.2f}")
                        if rec['propagated_risk'] >= 75:
                            st.error("🚨 **URGENT**\n\nImmediate executive attention required")
                        elif rec['propagated_risk'] >= 55:
                            st.warning("⚠️ **HIGH PRIORITY**\n\nInclude in next S&OP meeting")

            st.divider()

        # Regional recommendations
        if regional_recs:
            section_header("Regional Concentration Risks", icon="🌍")
            st.markdown(f"""
            <div style='background: rgba(139,92,246,0.1); border-left: 4px solid {COLORS['purple']};
                        padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <p style='color: #cbd5e0; margin: 0;'>
                    <strong>Geographic Diversification Opportunities:</strong> The following regions show high
                    supplier concentration. Consider diversifying to reduce geographic risk exposure.
                </p>
            </div>
            """, unsafe_allow_html=True)

            for i, rec in enumerate(regional_recs, 1):
                with st.expander(f"{i}. {rec['region']} - {rec['concentration']:.1f}% concentration ({rec['supplier_count']} suppliers)"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Region:** {rec['region']}")
                        st.markdown(f"**Concentration:** {rec['concentration']:.1f}% of Tier-1/2 suppliers")
                        st.markdown(f"**Action:** {rec['action']}")
                        st.markdown(f"**Reason:** {rec['reason']}")
                    with c2:
                        st.markdown(f"**Supplier Count:** {rec['supplier_count']}")
                        st.markdown(f"**Timeline:** {rec['timeline']}")
                        if rec['concentration'] > 50:
                            st.error("🚨 Critical concentration")
                        elif rec['concentration'] > 40:
                            st.warning("⚠️ High concentration")

    # ── TAB 2: Timeline ───────────────────────────────────────
    with tab_timeline:
        section_header("Implementation Timeline", icon="📅")

        # Contract value at risk
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("🔴 Critical Priority", f"€{summary['critical_contract_value']:.2f}M")
            with c2:
                st.metric("🟠 High Priority", f"€{summary['high_contract_value']:.2f}M")
            with c3:
                total_act_val = summary['critical_contract_value'] + summary['high_contract_value']
                st.metric("💼 Total (Crit + High)", f"€{total_act_val:.2f}M")

        st.divider()

        st.info(f"""
        ### Phased Implementation Approach

        **Phase 1: Immediate (0-30 days) — {summary['critical_count']} actions**
        - Focus on suppliers with risk ≥ 75 and no backup
        - Establish emergency procurement protocols
        - Initiate backup supplier qualification process
        - Contract value at risk: €{summary['critical_contract_value']:.2f}M

        **Phase 2: Short-term (30-60 days) — {summary['high_count']} actions**
        - Qualify backup suppliers for critical components
        - Establish dual-sourcing agreements
        - Negotiate risk-sharing clauses in contracts
        - Contract value at risk: €{summary['high_contract_value']:.2f}M

        **Phase 3: Medium-term (60-90 days) — {summary['medium_count']} actions**
        - Diversify away from geographically concentrated regions
        - Review and update supplier risk assessments
        - Implement automated risk monitoring systems

        **Phase 4: Ongoing — {summary['watch_count']} items**
        - Monitor supplier financial health quarterly
        - Track geopolitical developments
        - Review and update risk scores semi-annually
        """)

        st.divider()

        # Next steps
        section_header("Recommended Next Steps", icon="🚀")
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"""
            **For Procurement Team:**

            1. ✅ Download full recommendation list
            2. ✅ Schedule supplier meetings for top {min(10, summary['critical_count'])} critical items
            3. ✅ Initiate RFQs for backup suppliers
            4. ✅ Review contract terms for risk-sharing
            5. ✅ Set up quarterly monitoring process
            """)
        with c2:
            st.success(f"""
            **For Executive Leadership:**

            1. ✅ Present to S&OP team next meeting
            2. ✅ Allocate €{summary['critical_contract_value'] * 0.15:.2f}M for backup programs
            3. ✅ Approve geographic diversification strategy
            4. ✅ Review insurance coverage adequacy
            5. ✅ Establish supply chain risk committee
            """)

    # ── TAB 3: Summary Dashboard ──────────────────────────────
    with tab_summary:
        section_header("Summary Dashboard", icon="📊")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.plotly_chart(_build_severity_donut(summary), use_container_width=True)
        with c2:
            st.markdown("### Key Metrics")
            st.markdown(f"""
            - **Total Recommendations:** {summary['total_recommendations']}
            - **Unique Suppliers:** {summary['unique_suppliers']}
            - **Unique Countries:** {summary['unique_countries']}
            - **Critical Contract Value:** €{summary['critical_contract_value']:.2f}M
            - **High Contract Value:** €{summary['high_contract_value']:.2f}M
            - **Total At-Risk Value:** €{summary['critical_contract_value'] + summary['high_contract_value']:.2f}M
            """)

        st.divider()

        # Export section
        section_header("Export Recommendations", icon="📥")

        df_recs = pd.DataFrame(recommendations)
        if not df_recs.empty:
            display_cols = ['severity', 'supplier_id', 'supplier_name', 'tier', 'country',
                            'component', 'action', 'reason', 'timeline',
                            'propagated_risk', 'contract_value']
            df_export = df_recs[display_cols].copy()
            df_export.columns = ['Priority', 'Supplier ID', 'Supplier Name', 'Tier', 'Country',
                                  'Component', 'Action', 'Reason', 'Timeline',
                                  'Risk Score', 'Contract Value (€M)']

            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown("**Download complete action plan for procurement team and S&OP meetings**")
            with c2:
                st.download_button("📥 Download CSV", df_export.to_csv(index=False),
                                    "supplier_risk_recommendations.csv", "text/csv", use_container_width=True)

        st.divider()

        # Call to action
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {COLORS['accent']} 0%, {COLORS['accent_light']} 100%);
                    padding: 2rem; border-radius: 12px; text-align: center; margin: 2rem 0;'>
            <h2 style='color: white; margin: 0 0 1rem 0;'>Ready to Take Action?</h2>
            <p style='color: rgba(255,255,255,0.9); font-size: 1.1rem; margin: 0;'>
                Download the recommendations, share with your team, and start building a more resilient supply chain today.
            </p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
