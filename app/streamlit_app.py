"""
SupplierShield - Streamlit Dashboard
Main entry point for the interactive dashboard.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import networkx as nx
import numpy as np

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import DataValidator
from src.network.builder import SupplierNetworkBuilder
from src.risk.scorer import RiskScorer
from src.risk.propagation import RiskPropagator
from src.risk.spof_detector import SPOFDetector
from shared_styles import inject_css, COLORS, PLOTLY_LAYOUT_DEFAULTS, section_header

# Page configuration
st.set_page_config(
    page_title="SupplierShield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_css()


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


@st.cache_data
def compute_network_layout(_graph):
    """Compute and cache spring layout positions for the network graph."""
    pos = nx.spring_layout(_graph, k=0.5, iterations=50, seed=42)
    return pos


def _build_gauge(avg_risk):
    """Build a gauge chart for the average risk score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_risk,
        number={'font': {'size': 48, 'family': 'JetBrains Mono', 'color': COLORS['text_primary']},
                'suffix': '/100'},
        delta={'reference': 50, 'increasing': {'color': COLORS['CRITICAL']},
               'decreasing': {'color': COLORS['LOW']}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': COLORS['text_muted'],
                     'tickfont': {'size': 11, 'color': COLORS['text_muted']}},
            'bar': {'color': COLORS['accent']},
            'bgcolor': 'rgba(255,255,255,0.03)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 35], 'color': 'rgba(34,197,94,0.18)'},
                {'range': [35, 55], 'color': 'rgba(234,179,8,0.18)'},
                {'range': [55, 75], 'color': 'rgba(249,115,22,0.18)'},
                {'range': [75, 100], 'color': 'rgba(239,68,68,0.18)'},
            ],
            'threshold': {
                'line': {'color': COLORS['CRITICAL'], 'width': 3},
                'thickness': 0.8,
                'value': 75,
            },
        },
        title={'text': "Average Network Risk", 'font': {'size': 16, 'color': COLORS['text_secondary']}},
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=320,
        margin=dict(t=60, b=20, l=30, r=30),
    )
    return fig


def _build_donut(categories, total_suppliers):
    """Build a donut chart for risk category distribution."""
    labels = list(categories.keys())
    values = list(categories.values())
    colors_list = [COLORS[cat] for cat in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors_list, line=dict(color='rgba(10,14,26,0.8)', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, family='Inter', color=COLORS['text_primary']),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>',
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{total_suppliers}</b><br><span style='font-size:12px;color:#94a3b8'>suppliers</span>",
        showarrow=False, font=dict(size=28, color=COLORS['text_primary'], family='JetBrains Mono'),
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=320,
        margin=dict(t=40, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5,
                    font=dict(size=12, color=COLORS['text_muted'])),
        title={'text': "Risk Category Distribution", 'font': {'size': 16, 'color': COLORS['text_secondary']}},
    )
    return fig


def _build_network_graph(graph, spofs, pos, filter_tiers=None, filter_categories=None):
    """Build an interactive Plotly network graph."""
    fig = go.Figure()

    # ── Edges ──
    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode='lines',
        line=dict(width=0.6, color='rgba(148,163,184,0.2)'),
        hoverinfo='skip', showlegend=False,
    ))

    # ── Nodes by category (for legend) ──
    cat_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    cat_nodes = {cat: [] for cat in cat_order}
    for node in graph.nodes():
        cat = graph.nodes[node].get('risk_category', 'LOW')
        cat_nodes[cat].append(node)

    for cat in cat_order:
        nodes = cat_nodes[cat]
        if not nodes:
            continue

        xs, ys, sizes, texts, hovers, borders, opacities = [], [], [], [], [], [], []
        for n in nodes:
            nd = graph.nodes[n]
            x, y = pos[n]
            risk = nd.get('risk_propagated', nd['risk_composite'])
            cv = nd.get('contract_value_eur_m', 1)
            is_spof = n in spofs

            # Determine opacity based on filters
            opacity = 1.0
            if filter_tiers and nd['tier'] not in filter_tiers:
                opacity = 0.15
            if filter_categories and cat not in filter_categories:
                opacity = 0.15

            xs.append(x)
            ys.append(y)
            sizes.append(max(8, min(30, cv * 4)))
            texts.append(nd['name'][:12] if opacity == 1.0 else "")
            hovers.append(
                f"<b>{nd['name']}</b> ({n})<br>"
                f"Tier: {nd['tier']} | {nd['country']}<br>"
                f"Risk: {risk:.1f} ({cat})<br>"
                f"Contract: €{cv:.2f}M<br>"
                f"{'💥 SPOF' if is_spof else '✓ Has backup'}"
            )
            borders.append('white' if is_spof else 'rgba(0,0,0,0)')
            opacities.append(opacity)

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode='markers+text',
            marker=dict(
                size=sizes,
                color=COLORS[cat],
                opacity=opacities,
                line=dict(color=borders, width=[2 if b == 'white' else 0 for b in borders]),
            ),
            text=texts,
            textposition='top center',
            textfont=dict(size=9, color=COLORS['text_muted']),
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hovers,
            name=cat,
            legendgroup=cat,
        ))

    # SPOF legend marker
    spof_nodes_in_graph = [n for n in spofs if n in graph.nodes()]
    if spof_nodes_in_graph:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(color='white', width=2)),
            name='SPOF (white ring)',
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        height=650,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        margin=dict(t=30, b=20, l=20, r=20),
        legend=dict(
            bgcolor='rgba(13,18,32,0.85)',
            bordercolor='rgba(249,115,22,0.3)',
            borderwidth=1,
            font=dict(size=12, color=COLORS['text_muted']),
            itemsizing='constant',
        ),
        dragmode='pan',
    )
    return fig


def main():
    """Main dashboard home page."""

    # Sidebar
    st.sidebar.title("🛡️ SupplierShield")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Multi-Tier Supplier Risk Analyzer**")
    st.sidebar.markdown("")

    st.sidebar.info("""
    📍 **Navigate the Dashboard:**

    📊 **Risk Rankings**
    View and filter all suppliers

    🎲 **What-If Simulator**
    Run disruption scenarios

    📈 **Sensitivity Analysis**
    Criticality rankings

    📋 **Recommendations**
    Actionable risk mitigation plan
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Built by Andrei**")
    st.sidebar.markdown("HBO University Venlo, 2026")

    # Hero Section
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size: 3.5rem; margin-bottom: 0;'>🛡️ SupplierShield</h1>
            <p style='font-size: 1.35rem; color: #94a3b8; margin-top: 0.5rem; font-weight: 500;'>
                Multi-Tier Supplier Risk & Resilience Analyzer
            </p>
            <p style='font-size: 0.95rem; color: #64748b; margin-top: 0.75rem; letter-spacing: 0.05em;'>
                Graph Theory • Monte Carlo Simulation • Network Analysis
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Load data
    with st.spinner("🔄 Loading supplier network and calculating risks..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks, spofs = calculate_risks(graph)

    # Welcome message
    st.success(f"✅ **Network Loaded Successfully** • {graph.number_of_nodes()} suppliers • {graph.number_of_edges()} dependencies • 5-dimensional risk scoring complete")

    # ── Pre-compute shared data ──
    categories = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
    for node in graph.nodes():
        cat = graph.nodes[node].get('risk_category', 'UNKNOWN')
        if cat in categories:
            categories[cat] += 1

    avg_risk = sum(
        graph.nodes[n].get('risk_propagated', graph.nodes[n]['risk_composite'])
        for n in graph.nodes()
    ) / graph.number_of_nodes()

    critical_count = categories.get('CRITICAL', 0)

    # ── KPI Cards ──
    section_header("Network Overview", icon="📊")

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="📦 Total Suppliers", value=graph.number_of_nodes(),
                       help="Across 3 tiers (Tier-1, Tier-2, Tier-3)")
        with col2:
            st.metric(label="🔴 Critical Risk", value=critical_count,
                       delta=f"{critical_count / graph.number_of_nodes() * 100:.1f}% of network",
                       help="Suppliers with risk score ≥ 75")
        with col3:
            st.metric(label="⚠️ SPOFs Detected", value=len(spofs),
                       delta=f"{len(spofs) / graph.number_of_nodes() * 100:.1f}% of network",
                       help="Single Points of Failure - suppliers with no backup and high risk")
        with col4:
            st.metric(label="📊 Avg Risk Score", value=f"{avg_risk:.1f}", delta="/100",
                       help="Average propagated risk across entire network")

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # TABS: Risk Overview | Network Graph
    # ═══════════════════════════════════════════════════════════
    tab_overview, tab_network = st.tabs(["Risk Overview", "Network Graph"])

    # ── TAB 1: Risk Overview ──────────────────────────────────
    with tab_overview:

        # Gauge + Donut side by side
        col_gauge, col_donut = st.columns(2)
        with col_gauge:
            st.plotly_chart(_build_gauge(avg_risk), use_container_width=True)
        with col_donut:
            st.plotly_chart(_build_donut(categories, graph.number_of_nodes()), use_container_width=True)

        st.divider()

        # Tier breakdown
        section_header("Supply Chain Tier Breakdown", icon="🔢")
        tier_cols = st.columns(3)
        tier_colors_map = {1: COLORS['tier_1'], 2: COLORS['tier_2'], 3: COLORS['tier_3']}

        for i, tier in enumerate([1, 2, 3]):
            tier_nodes = [n for n in graph.nodes() if graph.nodes[n]['tier'] == tier]
            tier_avg = sum(
                graph.nodes[n].get('risk_propagated', graph.nodes[n]['risk_composite'])
                for n in tier_nodes
            ) / len(tier_nodes) if tier_nodes else 0
            tc = tier_colors_map[tier]

            with tier_cols[i]:
                st.markdown(f"""
                <div style='margin:0.5rem 0; padding:1rem; background:rgba(255,255,255,0.02);
                            border-left:4px solid {tc}; border-radius:6px;'>
                    <span style='font-size:1.1rem;'><strong>Tier-{tier}</strong></span><br/>
                    <span style='color:#94a3b8; font-size:0.9rem;'>
                        {len(tier_nodes)} suppliers • Avg Risk:
                        <span style='color:{tc}; font-weight:600;'>{tier_avg:.1f}</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Network Statistics
        section_header("Network Statistics", icon="🔬")

        with st.container(border=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 📐 Graph Metrics")
                density = graph.number_of_edges() / (graph.number_of_nodes() * (graph.number_of_nodes() - 1))
                st.markdown(f"""
                - **Nodes:** {graph.number_of_nodes()}
                - **Edges:** {graph.number_of_edges()}
                - **Avg Degree:** {graph.number_of_edges() / graph.number_of_nodes():.2f}
                - **Network Density:** {density:.4f}
                """)

            with col2:
                st.markdown("### 🔄 Risk Propagation")
                increased_count = sum(
                    1 for n in graph.nodes()
                    if graph.nodes[n].get('risk_propagated', 0) > graph.nodes[n]['risk_composite']
                )
                avg_increase = sum(
                    graph.nodes[n].get('risk_propagated', 0) - graph.nodes[n]['risk_composite']
                    for n in graph.nodes()
                    if graph.nodes[n].get('risk_propagated', 0) > graph.nodes[n]['risk_composite']
                ) / max(increased_count, 1)
                st.markdown(f"""
                - **Suppliers Affected:** {increased_count} ({increased_count / graph.number_of_nodes() * 100:.1f}%)
                - **Avg Risk Increase:** +{avg_increase:.2f} points
                - **Hidden Vulnerabilities:** Tier-1 suppliers exposed to Tier-2/3 risks
                """)

            with col3:
                st.markdown("### ⚠️ Critical Issues")
                critical_spofs = sum(
                    1 for s in spofs
                    if graph.nodes[s].get('risk_propagated', graph.nodes[s]['risk_composite']) >= 60
                )
                st.markdown(f"""
                - **Total SPOFs:** {len(spofs)}
                - **High-Risk SPOFs:** {critical_spofs}
                - **Action Required:** Immediate backup qualification needed
                """)

        st.divider()

        # Key Insight Highlight
        section_header("Key Insight: Hidden Dependencies", icon="💡")

        st.warning("""
        **⚡ Risk Propagation Example:**

        A Swiss supplier might appear "low risk" based on country stability alone. But if it depends on a
        high-risk Tier-2 supplier in DR Congo, the propagation algorithm reveals the true vulnerability:

        - **Composite Risk:** 16.4/100 (looks safe ✓)
        - **Propagated Risk:** 39.9/100 (actually medium risk ⚠️)
        - **Risk Increase:** +23.4 points (+143%)

        Traditional analysis misses this. SupplierShield catches it.
        """)

        st.divider()

        # Getting Started Guide
        section_header("Getting Started", icon="🚀")

        st.info("""
        **🎯 Explore the Dashboard:**

        1. **📊 Risk Rankings** → View and filter all 120 suppliers by risk level, tier, country, and SPOF status.
           Sort by propagated risk to identify the most vulnerable suppliers.

        2. **🎲 What-If Simulator** → Run Monte Carlo simulations (1,000-10,000 iterations) to estimate revenue
           impact of supplier failures. Test single-supplier or regional disruption scenarios.

        3. **📈 Sensitivity Analysis** → Discover which suppliers are most critical using the formula:
           **Criticality = Risk × Revenue Exposure**. Find the Pareto suppliers driving 50-80% of total risk.

        4. **📋 Recommendations** → Get a prioritized action plan with severity levels (CRITICAL/HIGH/MEDIUM/WATCH)
           and implementation timelines (0-30 days, 30-60 days, 60-90 days, ongoing).

        💡 **Pro Tip:** Start with the What-If Simulator to understand potential impacts, then use Recommendations
        to build your mitigation strategy.
        """)

    # ── TAB 2: Network Graph ─────────────────────────────────
    with tab_network:

        section_header("Interactive Supply Chain Network",
                        subtitle="Nodes sized by contract value, colored by risk category. White rings = SPOFs.",
                        icon="🌐")

        # Sidebar filters for network
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🌐 Network Filters")

        tier_filter = st.sidebar.multiselect(
            "Filter by Tier",
            options=[1, 2, 3],
            default=[1, 2, 3],
            format_func=lambda t: f"Tier-{t}",
            help="Dim nodes not in selected tiers"
        )

        cat_filter = st.sidebar.multiselect(
            "Filter by Risk Category",
            options=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            default=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            help="Dim nodes not in selected categories"
        )

        # Compute layout (cached)
        pos = compute_network_layout(graph)

        # Build and render graph
        net_fig = _build_network_graph(
            graph, spofs, pos,
            filter_tiers=tier_filter if len(tier_filter) < 3 else None,
            filter_categories=cat_filter if len(cat_filter) < 4 else None,
        )
        st.plotly_chart(net_fig, use_container_width=True, config={'scrollZoom': True})

        # Network stats summary
        with st.container(border=True):
            nc1, nc2, nc3, nc4 = st.columns(4)
            with nc1:
                st.metric("Nodes", graph.number_of_nodes())
            with nc2:
                st.metric("Edges", graph.number_of_edges())
            with nc3:
                st.metric("SPOFs", len(spofs))
            with nc4:
                st.metric("Avg Degree", f"{graph.number_of_edges() / graph.number_of_nodes():.1f}")

    # ── Footer ──
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #5a6478; padding: 2rem 0; border-top: 1px solid rgba(249, 115, 22, 0.2); margin-top: 1rem;'>
        <p style='font-size: 0.9rem; margin-bottom: 0.5rem;'>
            <strong>SupplierShield v1.0</strong> | Built with Python • NetworkX • Streamlit
        </p>
        <p style='font-size: 0.85rem; color: #64748b;'>
            © 2026 Andrei | HBO University Venlo, Netherlands | International Business Program
        </p>
        <p style='font-size: 0.8rem; color: #475569; margin-top: 0.5rem;'>
            Graph Theory • Monte Carlo Simulation • Multi-Dimensional Risk Scoring • Network Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
