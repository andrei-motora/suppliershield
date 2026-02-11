"""
Shared styles, colors, and helpers for the SupplierShield dashboard.
Centralizes CSS, Plotly defaults, and reusable UI components.
"""

import streamlit as st


# ── Color Constants ──────────────────────────────────────────────

COLORS = {
    # Brand / accent
    'accent': '#f97316',
    'accent_light': '#fb923c',
    'accent_lighter': '#fdba74',

    # Risk categories
    'CRITICAL': '#ef4444',
    'HIGH': '#f97316',
    'MEDIUM': '#eab308',
    'LOW': '#22c55e',

    # Tier colors
    'tier_1': '#3b82f6',
    'tier_2': '#8b5cf6',
    'tier_3': '#ec4899',

    # Text
    'text_primary': '#f7fafc',
    'text_secondary': '#e2e8f0',
    'text_muted': '#94a3b8',
    'text_dim': '#64748b',
    'text_dark': '#475569',

    # Backgrounds
    'bg_dark': '#0a0e1a',
    'bg_card': 'rgba(255, 255, 255, 0.02)',
    'bg_sidebar': '#0d1220',
    'plot_bg': 'rgba(10, 14, 26, 0.5)',
    'paper_bg': 'rgba(10, 14, 26, 0)',

    # Misc
    'purple': '#8b5cf6',
    'purple_light': '#a78bfa',
    'border_subtle': 'rgba(255, 255, 255, 0.05)',
}


# ── Plotly Layout Defaults ───────────────────────────────────────

PLOTLY_LAYOUT_DEFAULTS = dict(
    template='plotly_dark',
    plot_bgcolor=COLORS['plot_bg'],
    paper_bgcolor=COLORS['paper_bg'],
    font=dict(family='Inter, -apple-system, BlinkMacSystemFont, sans-serif',
              color=COLORS['text_muted']),
    title_font=dict(family='Inter', color=COLORS['text_secondary'], size=18),
)


# ── CSS Injection ────────────────────────────────────────────────

def inject_css():
    """Inject the full shared CSS block. Call once at the top of every page."""
    st.markdown("""
<style>
    /* ─── Fonts ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    /* ─── Main background ─── */
    .main {
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 50%, #0a0e1a 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ─── Sidebar ─── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1220 0%, #1a1f35 100%);
        border-right: 1px solid rgba(249, 115, 22, 0.2);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
        background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ─── Headers ─── */
    h1 {
        color: #f7fafc;
        font-weight: 800;
        font-size: 3rem !important;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #f97316 0%, #fb923c 50%, #fdba74 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }
    h2 {
        color: #e2e8f0;
        font-weight: 700;
        font-size: 1.75rem !important;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #f97316;
        padding-left: 1rem;
    }
    h3 {
        color: #cbd5e0;
        font-weight: 600;
        font-size: 1.25rem !important;
        margin-top: 1.5rem;
    }

    /* ─── Metrics ─── */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(249, 115, 22, 0.2);
        border-color: rgba(249, 115, 22, 0.3);
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.25rem !important;
        font-weight: 700;
        background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
    }

    /* ─── Buttons ─── */
    .stButton > button {
        background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
        font-family: 'Inter', sans-serif;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(249, 115, 22, 0.4);
        background: linear-gradient(135deg, #fb923c 0%, #fdba74 100%);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
    }

    /* ─── Alerts ─── */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    [data-baseweb="notification"] {
        border-radius: 10px;
    }

    /* ─── DataFrames ─── */
    .dataframe {
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        border-radius: 8px;
        overflow: hidden;
    }

    /* ─── Expanders ─── */
    .streamlit-expanderHeader {
        background: rgba(249, 115, 22, 0.05);
        border-radius: 8px;
        font-weight: 600;
        border-left: 3px solid #f97316;
        transition: all 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(249, 115, 22, 0.1);
    }

    /* ─── Tabs ─── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
        padding: 0.35rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        color: #94a3b8;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #f97316 0%, #fb923c 100%) !important;
        color: white !important;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ─── Containers ─── */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(249, 115, 22, 0.15);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.02);
        padding: 0.25rem;
    }

    /* ─── Dividers ─── */
    hr {
        border: none;
        border-top: 1px solid rgba(249, 115, 22, 0.2);
        margin: 2rem 0;
    }

    /* ─── Section breathing room ─── */
    [data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.25rem;
    }

    /* ─── Custom cards ─── */
    .custom-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }

    /* ─── Scrollbar ─── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #1a1f35; }
    ::-webkit-scrollbar-thumb { background: #f97316; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #fb923c; }
</style>
""", unsafe_allow_html=True)


# ── Reusable UI Helpers ──────────────────────────────────────────

def section_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a styled section header with optional subtitle and icon."""
    icon_html = f"<span style='margin-right:0.5rem;'>{icon}</span>" if icon else ""
    sub_html = (
        f"<p style='color:#94a3b8; font-size:1rem; margin:0.25rem 0 0 0;'>{subtitle}</p>"
        if subtitle else ""
    )
    st.markdown(f"""
    <div style='margin-bottom:1.5rem;'>
        <h2 style='margin-top:1rem;'>{icon_html}{title}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def risk_badge(category: str, score: float = None) -> str:
    """Return an HTML badge string for a risk category (optionally with score)."""
    color = COLORS.get(category, COLORS['text_muted'])
    score_text = f" ({score:.1f})" if score is not None else ""
    return (
        f"<span style='"
        f"background:{color}22; color:{color}; "
        f"padding:0.25rem 0.75rem; border-radius:12px; "
        f"font-weight:600; font-size:0.875rem; "
        f"border:1px solid {color}44; "
        f"font-family:\"JetBrains Mono\",monospace;"
        f"'>{category}{score_text}</span>"
    )


def severity_badge(severity: str) -> str:
    """Return an HTML badge for a severity/priority level."""
    emojis = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'WATCH': '⚪'}
    color = COLORS.get(severity, COLORS['text_muted'])
    emoji = emojis.get(severity, '⚪')
    return (
        f"<span style='"
        f"background:{color}22; color:{color}; "
        f"padding:0.5rem 1rem; border-radius:20px; "
        f"font-weight:700; font-size:0.9rem; "
        f"border:2px solid {color}44; "
        f"display:inline-block; margin-bottom:0.5rem;"
        f"'>{emoji} {severity}</span>"
    )
