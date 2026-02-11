"""
Risk Rankings Page - View and filter all suppliers by risk.
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
from src.risk.spof_detector import SPOFDetector

# Add app directory so shared_styles can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_styles import inject_css, COLORS, PLOTLY_LAYOUT_DEFAULTS, section_header, risk_badge

st.set_page_config(page_title="Risk Rankings", page_icon="📊", layout="wide")
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
    spof_detector = SPOFDetector(_graph)
    spofs = spof_detector.detect_all_spofs()
    return risk_scores, propagated_risks, spofs


def _risk_cell_color(val):
    """Return background color for a numeric risk value."""
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
    else:
        return 'background-color: rgba(34, 197, 94, 0.15); color: #86efac'


def _spof_style(val):
    """Bold red for SPOF = Yes."""
    if val == 'Yes':
        return 'color: #ef4444; font-weight: 700'
    return ''


def _build_heatmap(graph, top_n=25):
    """Build a risk-dimension heatmap for the top N suppliers by propagated risk."""
    # Gather data
    rows = []
    for node_id in graph.nodes():
        nd = graph.nodes[node_id]
        rows.append({
            'supplier_id': node_id,
            'name': nd['name'],
            'propagated_risk': nd.get('risk_propagated', nd['risk_composite']),
            'Geopolitical': nd.get('risk_geopolitical', 0),
            'Nat. Disaster': nd.get('risk_natural_disaster', 0),
            'Financial': nd.get('risk_financial', 0),
            'Logistics': nd.get('risk_logistics', 0),
            'Concentration': nd.get('risk_concentration', 0),
        })

    hm_df = pd.DataFrame(rows).sort_values('propagated_risk', ascending=False).head(top_n)
    dimensions = ['Geopolitical', 'Nat. Disaster', 'Financial', 'Logistics', 'Concentration']
    z = hm_df[dimensions].values
    y_labels = [f"{row['supplier_id']} - {row['name'][:25]}" for _, row in hm_df.iterrows()]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=dimensions,
        y=y_labels,
        text=np.round(z, 1),
        texttemplate='%{text}',
        textfont=dict(size=11, family='JetBrains Mono'),
        colorscale=[
            [0, '#22c55e'],
            [0.35, '#86efac'],
            [0.55, '#fde047'],
            [0.75, '#fb923c'],
            [1.0, '#ef4444'],
        ],
        colorbar=dict(title='Score', tickfont=dict(color=COLORS['text_muted'])),
        hovertemplate='<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>',
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=max(450, top_n * 28),
        margin=dict(l=280, r=60, t=50, b=60),
        title={'text': f"Risk Dimensions — Top {top_n} Suppliers",
               'font': {'size': 18, 'color': COLORS['text_secondary']}},
        yaxis={'autorange': 'reversed'},
        xaxis={'side': 'top'},
    )
    return fig


def main():
    st.title("📊 Risk Rankings")
    st.markdown("### Comprehensive Supplier Risk Analysis")
    st.divider()

    # Load data
    with st.spinner("🔄 Loading supplier network..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks, spofs = calculate_risks(graph)

    # Build DataFrame
    data = []
    for node_id in graph.nodes():
        nd = graph.nodes[node_id]
        data.append({
            'Supplier ID': node_id,
            'Name': nd['name'],
            'Tier': nd['tier'],
            'Country': nd['country'],
            'Component': nd['component'],
            'Composite Risk': nd['risk_composite'],
            'Propagated Risk': nd.get('risk_propagated', nd['risk_composite']),
            'Category': nd.get('risk_category', 'UNKNOWN'),
            'Contract Value (€M)': nd['contract_value_eur_m'],
            'SPOF': 'Yes' if nd.get('is_spof', False) else 'No',
            'Has Backup': 'Yes' if nd.get('has_backup', False) else 'No',
            'Financial Health': nd.get('financial_health', 0),
        })
    df = pd.DataFrame(data)

    # ── Sidebar Filters ──
    st.sidebar.markdown("## 🎯 Filters")
    st.sidebar.markdown("---")

    tier_options = ['All'] + sorted(df['Tier'].unique().tolist())
    selected_tier = st.sidebar.selectbox("🔢 Tier", tier_options)

    category_options = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    selected_category = st.sidebar.selectbox("⚠️ Risk Category", category_options)

    spof_options = ['All', 'Yes', 'No']
    selected_spof = st.sidebar.selectbox("💥 SPOF Status", spof_options)

    country_options = ['All'] + sorted(df['Country'].unique().tolist())
    selected_country = st.sidebar.selectbox("🌍 Country", country_options)

    st.sidebar.markdown("---")
    min_risk = st.sidebar.slider("Minimum Propagated Risk", 0, 100, 0)

    st.sidebar.markdown("---")
    sort_options = {
        'Propagated Risk (High to Low)': ('Propagated Risk', False),
        'Propagated Risk (Low to High)': ('Propagated Risk', True),
        'Composite Risk (High to Low)': ('Composite Risk', False),
        'Contract Value (High to Low)': ('Contract Value (€M)', False),
        'Supplier ID': ('Supplier ID', True),
        'Name (A-Z)': ('Name', True),
    }
    selected_sort = st.sidebar.selectbox("🔄 Sort By", list(sort_options.keys()))
    sort_col, sort_asc = sort_options[selected_sort]

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
    filtered_df = filtered_df[filtered_df['Propagated Risk'] >= min_risk]
    filtered_df = filtered_df.sort_values(sort_col, ascending=sort_asc).reset_index(drop=True)
    filtered_df.index = filtered_df.index + 1

    # ── Summary KPI row ──
    section_header(f"Results: {len(filtered_df)} suppliers", icon="🎯")

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Avg Propagated Risk", f"{filtered_df['Propagated Risk'].mean():.1f}",
                       delta=f"Range: {filtered_df['Propagated Risk'].min():.1f}–{filtered_df['Propagated Risk'].max():.1f}")
        with col2:
            spof_cnt = (filtered_df['SPOF'] == 'Yes').sum()
            st.metric("💥 SPOFs", spof_cnt,
                       delta=f"{spof_cnt / len(filtered_df) * 100:.1f}% of filtered" if len(filtered_df) > 0 else "0%")
        with col3:
            st.metric("💰 Total Contract Value", f"€{filtered_df['Contract Value (€M)'].sum():.1f}M",
                       delta=f"Avg: €{filtered_df['Contract Value (€M)'].mean():.2f}M")
        with col4:
            crit_cnt = (filtered_df['Category'] == 'CRITICAL').sum()
            st.metric("🔴 Critical Risk", crit_cnt,
                       delta=f"{crit_cnt / len(filtered_df) * 100:.1f}% of filtered" if len(filtered_df) > 0 else "0%")

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # TABS
    # ═══════════════════════════════════════════════════════════
    tab_table, tab_heatmap, tab_top10 = st.tabs(["Supplier Table", "Risk Heatmap", "Top 10 Analysis"])

    # ── TAB 1: Supplier Table ─────────────────────────────────
    with tab_table:
        if len(filtered_df) > 0:
            display_df = filtered_df.copy()
            display_df['Composite Risk'] = display_df['Composite Risk'].round(1)
            display_df['Propagated Risk'] = display_df['Propagated Risk'].round(1)
            display_df['Contract Value (€M)'] = display_df['Contract Value (€M)'].apply(lambda x: f"€{x:.2f}M")

            styled = (
                display_df.style
                .map(_risk_cell_color, subset=['Composite Risk', 'Propagated Risk'])
                .map(_spof_style, subset=['SPOF'])
                .apply(lambda row: ['background-color: rgba(239,68,68,0.12)'] * len(row)
                       if row['Category'] == 'CRITICAL'
                       else (['background-color: rgba(249,115,22,0.12)'] * len(row)
                             if row['Category'] == 'HIGH'
                             else (['background-color: rgba(234,179,8,0.10)'] * len(row)
                                   if row['Category'] == 'MEDIUM'
                                   else [''] * len(row))),
                       axis=1)
            )

            st.dataframe(styled, use_container_width=True, height=600)

            col_tip, col_dl = st.columns([3, 1])
            with col_tip:
                st.markdown(f"**💡 Tip:** {len(filtered_df)} suppliers match your filters. Adjust filters in the sidebar to refine results.")
            with col_dl:
                st.download_button("📥 Download CSV", filtered_df.to_csv(index=False),
                                    "supplier_risk_rankings.csv", "text/csv")
        else:
            st.warning("⚠️ No suppliers match your current filters. Try adjusting the criteria.")

    # ── TAB 2: Risk Heatmap ───────────────────────────────────
    with tab_heatmap:
        section_header("5-Dimension Risk Heatmap",
                        subtitle="Geopolitical, Natural Disaster, Financial, Logistics, Concentration scores for top suppliers",
                        icon="🗺️")

        hm_n = st.select_slider("Number of suppliers to show", options=[10, 15, 20, 25, 30, 40, 50], value=25)
        st.plotly_chart(_build_heatmap(graph, top_n=hm_n), use_container_width=True)

    # ── TAB 3: Top 10 Analysis ────────────────────────────────
    with tab_top10:
        section_header("Top 10 Highest Risk Suppliers", icon="🔴")

        top_10 = df.nlargest(10, 'Propagated Risk')[
            ['Supplier ID', 'Name', 'Tier', 'Country', 'Component',
             'Propagated Risk', 'Category', 'SPOF', 'Contract Value (€M)']
        ]

        for idx, row in top_10.iterrows():
            badge = risk_badge(row['Category'], row['Propagated Risk'])
            spof_text = "💥 <strong>SPOF</strong>" if row['SPOF'] == 'Yes' else "✓ Has backup"

            with st.expander(
                f"#{idx + 1} • {row['Supplier ID']} - {row['Name']} • Risk: {row['Propagated Risk']:.1f}",
                expanded=(idx == top_10.index[0])
            ):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("### 📋 Details")
                    st.markdown(f"**Supplier ID:** {row['Supplier ID']}")
                    st.markdown(f"**Name:** {row['Name']}")
                    st.markdown(f"**Component:** {row['Component']}")
                with c2:
                    st.markdown("### 🌍 Location")
                    st.markdown(f"**Country:** {row['Country']}")
                    st.markdown(f"**Tier:** {row['Tier']}")
                    st.markdown(f"**Contract:** €{row['Contract Value (€M)']:.2f}M")
                with c3:
                    st.markdown("### ⚠️ Risk Assessment")
                    st.markdown(f"**Risk Score:** {badge}", unsafe_allow_html=True)
                    st.markdown(f"**SPOF Status:** {spof_text}", unsafe_allow_html=True)
                    if row['SPOF'] == 'Yes':
                        st.error("🚨 **IMMEDIATE ACTION REQUIRED**\n\nQualify backup supplier within 30 days")
                    elif row['Propagated Risk'] >= 55:
                        st.warning("⚠️ **ACTION RECOMMENDED**\n\nReview supplier and consider dual-sourcing")

        st.divider()

        # Risk distribution summary
        section_header("Risk Distribution Breakdown", icon="📊")

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### By Category")
                cat_counts = df['Category'].value_counts()
                for cat in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    cnt = cat_counts.get(cat, 0)
                    pct = cnt / len(df) * 100
                    emojis = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                    st.markdown(f"{emojis[cat]} **{cat}:** {cnt} ({pct:.1f}%)")
            with c2:
                st.markdown("### By SPOF Status")
                s_cnt = (df['SPOF'] == 'Yes').sum()
                ns_cnt = (df['SPOF'] == 'No').sum()
                st.markdown(f"💥 **SPOFs:** {s_cnt} ({s_cnt / len(df) * 100:.1f}%)")
                st.markdown(f"✓ **Non-SPOFs:** {ns_cnt} ({ns_cnt / len(df) * 100:.1f}%)")


if __name__ == "__main__":
    main()
