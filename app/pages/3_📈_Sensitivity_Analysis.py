"""
Sensitivity Analysis Page - Criticality ranking of suppliers.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
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

# Add app directory so shared_styles can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_styles import inject_css, COLORS, PLOTLY_LAYOUT_DEFAULTS, section_header

st.set_page_config(page_title="Sensitivity Analysis", page_icon="📈", layout="wide")
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
def get_criticality_ranking(_graph, _product_bom):
    analyzer = SensitivityAnalyzer(graph=_graph, product_bom_df=_product_bom)
    ranking = analyzer.calculate_criticality_ranking()
    pareto = analyzer.get_pareto_analysis()
    tier_stats = analyzer.analyze_by_tier()
    country_stats = analyzer.analyze_by_country(top_n=10)
    return ranking, pareto, tier_stats, country_stats


def _get_risk_cat(risk_val):
    if risk_val >= 75:
        return 'CRITICAL'
    elif risk_val >= 55:
        return 'HIGH'
    elif risk_val >= 35:
        return 'MEDIUM'
    return 'LOW'


def _risk_cell_color(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ''
    if v >= 75:
        return 'background-color: rgba(239, 68, 68, 0.25); color: #fca5a5'
    elif v >= 55:
        return 'background-color: rgba(249, 115, 22, 0.25); color: #fdba74'
    elif v >= 35:
        return 'background-color: rgba(234, 179, 8, 0.20); color: #fde047'
    return 'background-color: rgba(34, 197, 94, 0.15); color: #86efac'


def _build_treemap(ranking, top_n=50):
    """Build a hierarchical treemap: Root → Tier → Supplier."""
    top = ranking.head(top_n).copy()
    top['risk_category'] = top['propagated_risk'].apply(_get_risk_cat)

    labels, parents, values, colors, hovers = [], [], [], [], []

    # Root
    labels.append("All Suppliers")
    parents.append("")
    values.append(0)
    colors.append(COLORS['bg_dark'])
    hovers.append("")

    # Tier nodes
    for tier in sorted(top['tier'].unique()):
        tier_label = f"Tier-{tier}"
        labels.append(tier_label)
        parents.append("All Suppliers")
        values.append(0)
        tc = {1: COLORS['tier_1'], 2: COLORS['tier_2'], 3: COLORS['tier_3']}
        colors.append(tc.get(tier, COLORS['text_muted']))
        hovers.append(f"<b>{tier_label}</b>")

    # Supplier leaves
    for _, row in top.iterrows():
        lbl = f"{row['supplier_id']}<br>{row['name'][:20]}"
        labels.append(lbl)
        parents.append(f"Tier-{row['tier']}")
        values.append(max(row['criticality_score'], 0.1))
        colors.append(COLORS.get(row['risk_category'], COLORS['text_muted']))
        hovers.append(
            f"<b>{row['name']}</b> ({row['supplier_id']})<br>"
            f"Criticality: {row['criticality_score']:.2f}<br>"
            f"Risk: {row['propagated_risk']:.1f} ({row['risk_category']})<br>"
            f"Revenue Exposure: €{row['total_revenue_exposure']:.2f}M"
        )

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors, line=dict(color='rgba(10,14,26,0.8)', width=1.5)),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hovers,
        textinfo='label',
        textfont=dict(size=11, family='Inter', color='white'),
        branchvalues='total',
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=600,
        margin=dict(t=40, b=20, l=20, r=20),
        title={'text': f"Criticality Treemap — Top {top_n} Suppliers",
               'font': {'size': 18, 'color': COLORS['text_secondary']}},
    )
    return fig


def _build_bubble_chart(ranking):
    """Build a scatter/bubble risk matrix: X=risk, Y=revenue, size=criticality."""
    df = ranking.copy()
    df['risk_category'] = df['propagated_risk'].apply(_get_risk_cat)

    # Quadrant thresholds
    risk_thresh = 60
    exposure_thresh = float(np.percentile(df['total_revenue_exposure'].dropna(), 75))

    fig = go.Figure()

    for cat in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        sub = df[df['risk_category'] == cat]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub['propagated_risk'],
            y=sub['total_revenue_exposure'],
            mode='markers',
            marker=dict(
                size=np.clip(sub['criticality_score'] * 2, 6, 40),
                color=COLORS[cat],
                opacity=0.8,
                line=dict(color='rgba(255,255,255,0.3)', width=1),
            ),
            name=cat,
            hovertemplate=(
                '<b>%{customdata[0]}</b> (%{customdata[1]})<br>'
                'Risk: %{x:.1f} | Exposure: €%{y:.2f}M<br>'
                'Criticality: %{customdata[2]:.2f}<extra></extra>'
            ),
            customdata=list(zip(sub['name'], sub['supplier_id'],
                                sub['criticality_score'])),
        ))

    # Quadrant lines
    fig.add_hline(y=exposure_thresh, line_dash="dot", line_color="rgba(148,163,184,0.4)", line_width=1)
    fig.add_vline(x=risk_thresh, line_dash="dot", line_color="rgba(148,163,184,0.4)", line_width=1)

    # DANGER ZONE annotation
    fig.add_annotation(
        x=85, y=exposure_thresh * 1.3,
        text="<b>DANGER ZONE</b>",
        showarrow=False,
        font=dict(size=14, color=COLORS['CRITICAL'], family='Inter'),
        opacity=0.7,
    )

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=550,
        xaxis_title="Propagated Risk Score",
        yaxis_title="Revenue Exposure (€M)",
        title={'text': "Risk × Revenue Exposure Matrix",
               'font': {'size': 18, 'color': COLORS['text_secondary']}},
        legend=dict(font=dict(size=12, color=COLORS['text_muted'])),
    )
    return fig


def main():
    st.title("📈 Sensitivity Analysis")
    st.markdown("### Criticality Ranking: Risk × Revenue Exposure")
    st.divider()

    # Load data
    with st.spinner("🔄 Calculating criticality scores..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks = calculate_risks(graph)
        ranking, pareto, tier_stats, country_stats = get_criticality_ranking(graph, product_bom)

    st.success("✅ **Analysis Complete!** Criticality calculated for all 120 suppliers")

    # ── Pareto Analysis ──
    section_header("Pareto Analysis: The Power Law", icon="🎯")

    st.markdown(f"""
    <div style='background: rgba(249, 115, 22, 0.08); border-left: 4px solid {COLORS['accent']}; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;'>
        <h3 style='color: {COLORS['accent']}; margin-top: 0;'>The 80/20 Rule in Supply Chain Risk</h3>
        <p style='color: #cbd5e0; font-size: 1.05rem;'>
            A small percentage of suppliers drive the majority of your risk. Focus mitigation efforts here for maximum impact.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🎯 50% of Total Risk", f"{pareto['pareto_50_suppliers']} suppliers",
                       delta=f"{pareto['pareto_50_percent']:.1f}% of network")
        with c2:
            st.metric("📊 80% of Total Risk", f"{pareto['pareto_80_suppliers']} suppliers",
                       delta=f"{pareto['pareto_80_percent']:.1f}% of network")
        with c3:
            st.metric("🏆 Top 10 Concentration", f"{pareto['top_10_percent']:.1f}%",
                       delta="of total criticality")

    st.info(f"""
    💡 **Key Insight:** Just **{pareto['pareto_50_suppliers']} suppliers ({pareto['pareto_50_percent']:.1f}% of network)**
    drive **50% of your total risk exposure**.

    Start your risk mitigation program with these suppliers. Qualifying backups for just these
    {pareto['pareto_50_suppliers']} suppliers will cut your risk in half!
    """)

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # PRIMARY TABS: Criticality Ranking | Treemap | Risk Matrix
    # ═══════════════════════════════════════════════════════════
    tab_rank, tab_tree, tab_matrix = st.tabs(["Criticality Ranking", "Treemap", "Risk Matrix"])

    # ── TAB 1: Criticality Ranking ────────────────────────────
    with tab_rank:
        section_header("Top Critical Suppliers", icon="🏆")

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown("**Ranked by: Criticality = Risk Score × Revenue Exposure**")
        with c2:
            top_n = st.selectbox("Show top:", [10, 20, 30, 50], index=1)

        top_suppliers = ranking.head(top_n)

        # Bar chart
        colors_list = [COLORS[_get_risk_cat(r)] for r in top_suppliers['propagated_risk']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=[f"{row['supplier_id']} - {row['name'][:30]}" for _, row in top_suppliers.iterrows()],
            x=top_suppliers['criticality_score'],
            orientation='h',
            marker=dict(color=colors_list, line=dict(color='rgba(255,255,255,0.3)', width=1.5)),
            text=[f"{s:.1f}" for s in top_suppliers['criticality_score']],
            textposition='outside',
            textfont=dict(family="JetBrains Mono", size=11, color=COLORS['text_secondary']),
            hovertemplate='<b>%{y}</b><br>Criticality: %{x:.2f}<extra></extra>',
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            title={'text': f"Top {top_n} Most Critical Suppliers"},
            xaxis_title="Criticality Score",
            yaxis_title="",
            height=max(500, top_n * 25),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(l=300, r=100, t=80, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Detailed table with enhanced styling
        section_header(f"Top {top_n} Suppliers — Detailed Breakdown", icon="📋")

        display_cols = ['supplier_id', 'name', 'tier', 'country', 'component',
                        'criticality_score', 'propagated_risk', 'total_revenue_exposure',
                        'affected_products', 'downstream_suppliers']
        display_df = top_suppliers[display_cols].copy()
        display_df.columns = ['ID', 'Name', 'Tier', 'Country', 'Component',
                               'Criticality', 'Risk', 'Exposure (€M)', 'Products', 'Downstream']

        # Style numeric columns
        styled = (
            display_df.style
            .format({'Criticality': '{:.2f}', 'Risk': '{:.1f}', 'Exposure (€M)': '€{:.2f}M'})
            .map(_risk_cell_color, subset=['Risk'])
        )
        st.dataframe(styled, use_container_width=True, height=400)

        st.download_button(f"📥 Download Top {top_n} as CSV", top_suppliers.to_csv(index=False),
                            f"top_{top_n}_critical_suppliers.csv", "text/csv")

    # ── TAB 2: Treemap ───────────────────────────────────────
    with tab_tree:
        section_header("Criticality Treemap",
                        subtitle="Hierarchy: Root → Tier → Supplier. Rectangle area = criticality score, color = risk category.",
                        icon="🌳")
        tree_n = st.select_slider("Number of suppliers", options=[20, 30, 40, 50], value=50, key="tree_n")
        st.plotly_chart(_build_treemap(ranking, top_n=tree_n), use_container_width=True)

    # ── TAB 3: Risk Matrix ───────────────────────────────────
    with tab_matrix:
        section_header("Risk × Revenue Exposure Matrix",
                        subtitle="Bubble size = criticality score. Top-right quadrant = highest priority.",
                        icon="🎯")
        st.plotly_chart(_build_bubble_chart(ranking), use_container_width=True)

        st.markdown(f"""
        <div style='background: rgba(239,68,68,0.08); border-left: 4px solid {COLORS["CRITICAL"]};
                    padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
            <p style='color: #cbd5e0; margin: 0;'>
                <strong>Interpretation:</strong> Suppliers in the top-right <b>DANGER ZONE</b> have both
                high risk scores and large revenue exposure — they should be your highest priority for
                backup qualification and dual-sourcing strategies.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # SECONDARY TABS: Country Ranking | Tier Comparison
    # ═══════════════════════════════════════════════════════════
    tab_country, tab_tier = st.tabs(["Country Ranking", "Tier Comparison"])

    # ── Country Ranking ───────────────────────────────────────
    with tab_country:
        section_header("Geographic Risk Concentration", icon="🌍")

        country_display = country_stats.head(10).copy()
        country_display['Total Criticality'] = country_display['Total Criticality'].apply(lambda x: f"{x:.2f}")
        country_display['Supplier Count'] = country_display['Supplier Count'].astype(int)
        country_display['Avg Criticality'] = country_display['Avg Criticality'].apply(lambda x: f"{x:.2f}")
        country_display['Avg Risk'] = country_display['Avg Risk'].apply(lambda x: f"{x:.1f}")
        st.dataframe(country_display, use_container_width=True, height=400)

        # Country bar chart
        country_colors = [f'rgba(249, 115, 22, {1 - i * 0.08})' for i in range(min(10, len(country_stats)))]
        fig_country = go.Figure()
        fig_country.add_trace(go.Bar(
            x=country_stats.index[:10],
            y=country_stats['Total Criticality'][:10],
            marker=dict(color=country_colors, line=dict(color=COLORS['accent'], width=2)),
            text=[f"{v:.1f}" for v in country_stats['Total Criticality'][:10]],
            textposition='outside',
            textfont=dict(family="JetBrains Mono", size=12, color=COLORS['text_secondary']),
            hovertemplate='<b>%{x}</b><br>Total Criticality: %{y:.2f}<extra></extra>',
        ))
        fig_country.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            title={'text': "Total Criticality by Country (Top 10)"},
            xaxis_title="Country", yaxis_title="Total Criticality Score",
            height=450, showlegend=False,
        )
        st.plotly_chart(fig_country, use_container_width=True)

        top_3 = country_stats.index[:3].tolist()
        top_3_pct = country_stats['Total Criticality'][:3].sum() / country_stats['Total Criticality'].sum() * 100
        st.warning(f"""
        ⚠️ **Geographic Concentration Risk**

        Top 3 countries ({', '.join(top_3)}) account for **{top_3_pct:.1f}%** of total criticality.

        **Recommended Action:** Diversify sourcing away from these concentrated regions.
        """)

    # ── Tier Comparison ───────────────────────────────────────
    with tab_tier:
        section_header("Analysis by Supply Chain Tier", icon="🔢")

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 📊 Tier Statistics")
                tier_display = tier_stats.copy()
                tier_display['Tier'] = tier_display['Tier'].astype(int)
                tier_display['Count'] = tier_display['Count'].astype(int)
                tier_display['Avg Criticality'] = tier_display['Avg Criticality'].apply(lambda x: f"{x:.2f}")
                tier_display['Max Criticality'] = tier_display['Max Criticality'].apply(lambda x: f"{x:.2f}")
                st.dataframe(tier_display, use_container_width=True, hide_index=True)

            with c2:
                st.markdown("### 📈 Tier Comparison")
                tier_color_map = {1: COLORS['tier_1'], 2: COLORS['tier_2'], 3: COLORS['tier_3']}
                bar_colors = [tier_color_map[int(t)] for t in tier_stats['Tier']]

                fig_tier = go.Figure()
                fig_tier.add_trace(go.Bar(
                    x=[f"Tier-{int(t)}" for t in tier_stats['Tier']],
                    y=tier_stats['Avg Criticality'],
                    marker=dict(color=bar_colors, line=dict(color='rgba(255,255,255,0.3)', width=2)),
                    text=[f"{v:.2f}" for v in tier_stats['Avg Criticality']],
                    textposition='outside',
                    textfont=dict(family="JetBrains Mono", size=14),
                    hovertemplate='<b>%{x}</b><br>Avg Criticality: %{y:.2f}<extra></extra>',
                ))
                fig_tier.update_layout(
                    **PLOTLY_LAYOUT_DEFAULTS,
                    title="Average Criticality by Tier",
                    yaxis_title="Average Criticality Score",
                    height=350, showlegend=False,
                )
                st.plotly_chart(fig_tier, use_container_width=True)

        highest_tier = tier_stats.loc[tier_stats['Avg Criticality'].idxmax(), 'Tier']
        highest_val = tier_stats.loc[tier_stats['Avg Criticality'].idxmax(), 'Avg Criticality']
        st.info(f"💡 **Insight:** Tier-{int(highest_tier)} has the highest average criticality ({highest_val:.2f}). Prioritize risk mitigation efforts on Tier-{int(highest_tier)} suppliers!")

    st.divider()

    # ── Methodology ──
    section_header("Understanding Criticality Score", icon="💡")

    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.info("""
            **Formula: Criticality = Risk Score × Revenue Exposure**

            This metric combines two critical dimensions:

            1. **Risk Score (0-100)** - How likely is this supplier to fail?
               - Based on geopolitical, disaster, financial, logistics, and concentration risk
               - Includes risk propagation from upstream dependencies

            2. **Revenue Exposure (€M)** - How much revenue is at stake?
               - Direct revenue from products using this supplier
               - Indirect revenue from downstream suppliers (50% weighted)

            **Why It Matters:**
            - A low-risk supplier with €50M exposure (criticality: 15) is more critical than a high-risk supplier with €1M exposure (criticality: 8)
            - Criticality helps you prioritize *where* to invest in risk mitigation for maximum ROI
            """)
        with c2:
            st.markdown("### 🎯 Action Thresholds")
            st.markdown("""
            **Criticality Score Ranges:**

            - **> 20:** 🔴 Critical — Immediate backup qualification
            - **15-20:** 🟠 High — Action within 30-60 days
            - **10-15:** 🟡 Medium — Quarterly monitoring
            - **< 10:** 🟢 Low — Standard monitoring
            """)


if __name__ == "__main__":
    main()
