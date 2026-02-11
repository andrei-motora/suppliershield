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

# Add app directory so shared_styles can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_styles import inject_css, COLORS, PLOTLY_LAYOUT_DEFAULTS, section_header

st.set_page_config(page_title="What-If Simulator", page_icon="🎲", layout="wide")
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


def main():
    st.title("🎲 What-If Simulator")
    st.markdown("### Monte Carlo Disruption Impact Analysis")
    st.divider()

    # Load data
    with st.spinner("🔄 Loading network and initializing simulator..."):
        suppliers, dependencies, country_risk, product_bom = load_data()
        graph = build_network(suppliers, dependencies, country_risk)
        risk_scores, propagated_risks = calculate_risks(graph)

    # Initialize simulator
    simulator = MonteCarloSimulator(graph=graph, product_bom_df=product_bom, seed=42)

    # ── Scenario configuration ──
    section_header("Configure Disruption Scenario", icon="⚙️")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Target Selection")

        scenario_type = st.selectbox(
            "Scenario Type",
            ['single_node', 'regional'],
            format_func=lambda x: {
                'single_node': '🎯 Single Supplier Failure',
                'regional': '🌍 Regional Disruption (All suppliers in region)'
            }[x],
        )

        if scenario_type == 'single_node':
            supplier_options = sorted([
                f"{node} - {graph.nodes[node]['name']} (Risk: {graph.nodes[node].get('risk_propagated', graph.nodes[node]['risk_composite']):.1f})"
                for node in graph.nodes()
            ], key=lambda x: float(x.split('Risk: ')[1].split(')')[0]), reverse=True)

            selected_supplier = st.selectbox("Select Supplier", supplier_options)
            target = selected_supplier.split(' - ')[0]

            st.info(f"""
            **Selected Supplier:**
            - **ID:** {target}
            - **Name:** {graph.nodes[target]['name']}
            - **Tier:** {graph.nodes[target]['tier']}
            - **Country:** {graph.nodes[target]['country']}
            - **Risk:** {graph.nodes[target].get('risk_propagated', graph.nodes[target]['risk_composite']):.1f}
            """)
        else:
            regions = sorted(set(graph.nodes[node]['region'] for node in graph.nodes()))
            selected_region = st.selectbox("Select Region", regions)
            region_suppliers = [n for n in graph.nodes() if graph.nodes[n]['region'] == selected_region]

            st.info(f"""
            **Selected Region:**
            - **Region:** {selected_region}
            - **Suppliers:** {len(region_suppliers)}
            - **Avg Risk:** {sum(graph.nodes[n].get('risk_propagated', graph.nodes[n]['risk_composite']) for n in region_suppliers) / len(region_suppliers):.1f}
            """)
            target = region_suppliers[0]

    with col2:
        st.markdown("### 📊 Simulation Parameters")

        duration = st.slider("Disruption Duration (days)", 7, 90, 30, step=7)
        iterations = st.select_slider("Monte Carlo Iterations",
                                       options=[1000, 2000, 3000, 5000, 10000], value=3000)

        st.info(f"""
        **Simulation Settings:**
        - **Duration:** {duration} days
        - **Iterations:** {iterations:,}
        - **Runtime:** ~{iterations / 1000:.1f}s estimated
        """)

    st.divider()

    # Run button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button("🚀 Run Monte Carlo Simulation", type="primary", use_container_width=True)

    if run_button:
        with st.spinner(f"🎲 Running {iterations:,} Monte Carlo iterations... Please wait."):
            results = simulator.run_simulation(
                target_supplier=target, duration_days=duration,
                iterations=iterations, scenario_type=scenario_type,
            )

        st.success(f"✅ **Simulation Complete!** Analyzed {iterations:,} scenarios in {results.get('runtime', 0):.2f}s")
        st.divider()

        # ── KPI cards ──
        section_header("Simulation Results", icon="📊")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("💰 Mean Impact", f"€{results['mean']:.2f}M")
            with c2:
                st.metric("📊 Median (P50)", f"€{results['median']:.2f}M",
                           delta=f"{((results['median'] - results['mean']) / results['mean'] * 100):.1f}% vs mean" if results['mean'] > 0 else "N/A")
            with c3:
                st.metric("⚠️ 95th Percentile", f"€{results['p95']:.2f}M",
                           delta=f"+€{results['p95'] - results['mean']:.2f}M", delta_color="inverse")
            with c4:
                st.metric("🔴 Worst Case", f"€{results['max']:.2f}M",
                           delta=f"+€{results['max'] - results['mean']:.2f}M", delta_color="inverse")

        st.divider()

        # ════════════════════════════════════════════════════
        # TABS: Impact Distribution | Statistics | Management Summary
        # ════════════════════════════════════════════════════
        tab_dist, tab_stats, tab_mgmt = st.tabs(["Impact Distribution", "Statistics", "Management Summary"])

        # ── TAB 1: Impact Distribution ────────────────────
        with tab_dist:
            hist_data = simulator.get_histogram_data(results['all_results'], bins=30)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=hist_data['bin_centers'], y=hist_data['counts'],
                marker=dict(
                    color=hist_data['bin_centers'],
                    colorscale=[[0, '#22c55e'], [0.3, '#eab308'], [0.6, '#f97316'], [1, '#ef4444']],
                    line=dict(color='rgba(255,255,255,0.2)', width=1),
                ),
                name='Frequency',
                hovertemplate='<b>Impact: €%{x:.2f}M</b><br>Frequency: %{y}<extra></extra>',
            ))

            fig.add_vline(x=results['mean'], line_dash="dash", line_color="#22c55e", line_width=3,
                           annotation=dict(text=f"Mean: €{results['mean']:.2f}M", showarrow=False, yshift=10,
                                           font=dict(size=12, color="#22c55e", family="JetBrains Mono")))
            fig.add_vline(x=results['p95'], line_dash="dash", line_color="#ef4444", line_width=3,
                           annotation=dict(text=f"P95: €{results['p95']:.2f}M", showarrow=False, yshift=10,
                                           font=dict(size=12, color="#ef4444", family="JetBrains Mono")))

            fig.update_layout(
                **PLOTLY_LAYOUT_DEFAULTS,
                title={'text': "Distribution of Revenue Impact Across All Scenarios",
                       'font': {'size': 18, 'color': COLORS['text_secondary']}},
                xaxis_title="Revenue Impact (€M)",
                yaxis_title="Number of Scenarios",
                height=500, showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── TAB 2: Statistics ─────────────────────────────
        with tab_stats:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### 📊 Central Tendency")
                    cv = f"{results['std'] / results['mean'] * 100:.1f}%" if results['mean'] > 0 else "N/A"
                    st.markdown(f"""
                    - **Mean:** €{results['mean']:.2f}M
                    - **Median:** €{results['median']:.2f}M
                    - **Mode:** €{results.get('mode', results['median']):.2f}M
                    - **Std Dev:** €{results['std']:.2f}M
                    - **Coefficient of Variation:** {cv}
                    """)
                with c2:
                    st.markdown("### ⚠️ Risk Percentiles")
                    st.markdown(f"""
                    - **P90 (1 in 10):** €{results['p90']:.2f}M
                    - **P95 (1 in 20):** €{results['p95']:.2f}M
                    - **P99 (1 in 100):** €{results['p99']:.2f}M
                    - **Maximum:** €{results['max']:.2f}M
                    - **Minimum:** €{results['min']:.2f}M
                    """)

            st.divider()

            # Scenario details
            section_header("Scenario Details", icon="📝")
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("### 🎯 Target")
                    if scenario_type == 'single_node':
                        st.markdown(f"**Supplier:** {target}")
                        st.markdown(f"**Name:** {graph.nodes[target]['name']}")
                        st.markdown(f"**Tier:** {graph.nodes[target]['tier']}")
                        st.markdown(f"**Country:** {graph.nodes[target]['country']}")
                    else:
                        st.markdown(f"**Region:** {selected_region}")
                        st.markdown(f"**Suppliers Affected:** {len(region_suppliers)}")
                with c2:
                    st.markdown("### ⚙️ Parameters")
                    st.markdown(f"**Scenario:** {scenario_type}")
                    st.markdown(f"**Duration:** {duration} days")
                    st.markdown(f"**Iterations:** {iterations:,}")
                    st.markdown(f"**Runtime:** {results.get('runtime', 0):.2f}s")
                with c3:
                    st.markdown("### 🎲 Impact Scope")
                    st.markdown(f"**Affected Suppliers:** {results['affected_suppliers_count']}")
                    st.markdown(f"**Affected Products:** {len(results.get('affected_products', []))}")
                    zero_pct = sum(1 for x in results['all_results'] if x == 0) / iterations * 100
                    st.markdown(f"**Zero Impact Scenarios:** {sum(1 for x in results['all_results'] if x == 0)} ({zero_pct:.1f}%)")

        # ── TAB 3: Management Summary ─────────────────────
        with tab_mgmt:
            # Severity indicator
            if results['mean'] > 20:
                sev_label, sev_color = "🔴 CRITICAL", COLORS['CRITICAL']
            elif results['mean'] > 10:
                sev_label, sev_color = "🟠 HIGH", COLORS['HIGH']
            elif results['mean'] > 5:
                sev_label, sev_color = "🟡 MEDIUM", COLORS['MEDIUM']
            else:
                sev_label, sev_color = "🟢 LOW", COLORS['LOW']

            st.markdown(f"""
            <div style='background: {sev_color}15; border-left: 4px solid {sev_color}; padding: 1.5rem; border-radius: 8px;'>
                <h3 style='color: {sev_color}; margin-top: 0;'>Impact Severity: {sev_label}</h3>
            </div>
            """, unsafe_allow_html=True)

            st.info(f"""
            **What These Numbers Mean:**

            🎯 **Expected Impact (Mean: €{results['mean']:.2f}M)**
            This is your planning baseline. On average, this disruption would cost €{results['mean']:.2f}M in lost revenue.
            Budget this amount for contingency planning.

            📊 **Typical Scenario (Median: €{results['median']:.2f}M)**
            Half of all scenarios result in losses below €{results['median']:.2f}M, half above. This is your "most likely" outcome.

            ⚠️ **Bad Luck Scenario (P95: €{results['p95']:.2f}M)**
            There's a 5% chance (1 in 20) that losses exceed €{results['p95']:.2f}M. This is your risk planning threshold.
            Set aside €{results['p95']:.2f}M in emergency reserves.

            🔴 **Worst Case (Max: €{results['max']:.2f}M)**
            Maximum observed impact across {iterations:,} simulations. While rare, this represents the upper bound of possible losses.

            **Recommended Actions:**
            - ✅ Set contingency budget: €{results['p95']:.2f}M
            - ✅ {"Qualify backup supplier immediately (0-30 days)" if results['mean'] > 10 else "Monitor supplier quarterly"}
            - ✅ {"Present to executive team - significant risk exposure" if results['mean'] > 15 else "Include in risk register"}
            - ✅ Review insurance coverage for disruptions > €{results['p95']:.2f}M
            """)


if __name__ == "__main__":
    main()
