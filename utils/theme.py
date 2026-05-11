import streamlit as st
import streamlit.components.v1 as components
import json
import textwrap
FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Syne:wght@400;600;700;800&"
    "family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600&"
    "family=JetBrains+Mono:wght@300;400;500;600&display=swap"
)

# ═════════════════════════════════════════════
# Theme & Sidebar Toggle System
# ═════════════════════════════════════════════
def init_session():
    """Initialize session state"""
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = 'dark'
    if 'sidebar_collapsed' not in st.session_state:
        st.session_state.sidebar_collapsed = False

def toggle_theme():
    """Toggle between light and dark mode"""
    st.session_state.theme_mode = 'light' if st.session_state.theme_mode == 'dark' else 'dark'

def toggle_sidebar():
    """Toggle sidebar collapse state"""
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed

def get_theme_colors():
    """Get color palette based on current theme"""
    if st.session_state.theme_mode == 'dark':
        return {
            'bg_primary':   '#070b12',
            'bg_surface':   '#0d1421',
            'bg_elevated':  '#121c30',
            'bg_card':      '#0f1929',
            'border':       'rgba(255,255,255,0.05)',
            'border_light': 'rgba(255,255,255,0.09)',
            'txt1':         '#dce8f7',
            'txt2':         '#7a90b0',
            'txt3':         '#3c506e',
            'plot_bg':      '#0d1421',
            'plot_grid':    'rgba(255,255,255,0.04)',
        }
    else:
        return {
            'bg_primary':   '#ffffff',
            'bg_surface':   '#f8f9fb',
            'bg_elevated':  '#ffffff',
            'bg_card':      '#ffffff',
            'border':       'rgba(0,0,0,0.08)',
            'border_light': 'rgba(0,0,0,0.12)',
            'txt1':         '#1a202c',
            'txt2':         '#4a5568',
            'txt3':         '#a0aec0',
            'plot_bg':      '#ffffff',
            'plot_grid':    'rgba(0,0,0,0.06)',
        }

# ═════════════════════════════════════════════
# Hybrid Top Bar + Collapsible Sidebar
# ═════════════════════════════════════════════
def render_hybrid_navbar(show_prediction_controls=False, currency="USD/IDR", model="ARIMA", mode="Tuning"):
    """Inject navbar via components.html() JavaScript only."""
    init_session()
    colors = get_theme_colors()

    theme_icon = "☀️" if st.session_state.theme_mode == 'dark' else "🌙"
    sidebar_width = "60px" if st.session_state.sidebar_collapsed else "220px"

    controls_html = ""
    if show_prediction_controls:
        controls_html = (
            f'<div class="gree-prediction-controls">'
            f'<span class="gree-control-badge">{currency}</span>'
            f'<span class="gree-control-badge">{model}</span>'
            f'<span class="gree-control-badge">{mode}</span>'
            f'</div>'
        )

    # CSS Khusus Navbar (Sembunyikan UI bawaan sudah dipindah ke inject_theme)
    css = (
        f'.gree-top-bar{{position:fixed;top:0;left:0;right:0;height:60px;'
        f'background:{colors["bg_card"]};border-bottom:1px solid {colors["border_light"]};'
        f'display:flex;align-items:center;justify-content:space-between;padding:0 1.5rem;'
        f'z-index:99999;backdrop-filter:blur(10px);box-shadow:0 2px 8px rgba(0,0,0,.06);'
        f'font-family:"DM Sans",sans-serif;box-sizing:border-box}}'
        f'.gree-top-bar-left{{display:flex;align-items:center;gap:1rem}}'
        f'.gree-hamburger{{font-size:1.4rem;cursor:pointer;color:{colors["txt2"]};'
        f'user-select:none;transition:color .2s}}'
        f'.gree-hamburger:hover{{color:#00d4aa}}'
        f'.gree-brand{{font-family:"Syne",sans-serif;font-size:1.3rem;font-weight:800;'
        f'color:{colors["txt1"]};letter-spacing:-.02em}}'
        f'.gree-prediction-controls{{display:flex;gap:.6rem;align-items:center}}'
        f'.gree-control-badge{{background:{colors["bg_surface"]};border:1px solid {colors["border"]};'
        f'border-radius:6px;padding:.35rem .75rem;font-size:.78rem;color:{colors["txt2"]};font-weight:500}}'
        f'.gree-theme-toggle{{background:{colors["bg_surface"]};border:1px solid {colors["border"]};'
        f'border-radius:8px;padding:.45rem .9rem;font-size:1.1rem;cursor:pointer;'
        f'user-select:none;transition:border-color .2s}}'
        f'.gree-theme-toggle:hover{{border-color:#00d4aa}}'
        f'.gree-nav-sidebar{{position:fixed;left:0;top:60px;bottom:0;width:{sidebar_width};'
        f'background:{colors["bg_surface"]};border-right:1px solid {colors["border_light"]};'
        f'transition:width .3s ease;overflow:hidden;z-index:99998}}'
        f'.gree-nav-item{{display:flex;align-items:center;gap:1rem;padding:.9rem 1.2rem;'
        f'color:{colors["txt2"]};text-decoration:none;font-family:"DM Sans",sans-serif;'
        f'font-size:.9rem;transition:all .2s;border-left:3px solid transparent;white-space:nowrap}}'
        f'.gree-nav-item:hover{{background:{colors["bg_elevated"]};color:#00d4aa;border-left-color:#00d4aa}}'
        f'.gree-nav-icon{{font-size:1.3rem;min-width:24px;text-align:center}}'
        f'[data-testid="stAppViewContainer"]>.main{{margin-left:{sidebar_width}!important;'
        f'margin-top:60px!important;padding:1.5rem 2rem!important;transition:margin-left .3s ease}}'
    )

    navbar_html = (
        f'<div class="gree-top-bar">'
        f'<div class="gree-top-bar-left">'
        f'<span class="gree-hamburger">&#9776;</span>'
        f'<span class="gree-brand">&#128184; BAM Board</span>'
        f'{controls_html}'
        f'</div>'
        f'<span class="gree-theme-toggle">{theme_icon}</span>'
        f'</div>'
        f'<nav class="gree-nav-sidebar">'
        f'<a href="/" target="_parent" class="gree-nav-item"><span class="gree-nav-icon">&#127968;</span><span>Home</span></a>'
        f'<a href="/prediction" target="_parent" class="gree-nav-item"><span class="gree-nav-icon">&#128302;</span><span>Prediction</span></a>'
        f'<a href="/eda" target="_parent" class="gree-nav-item"><span class="gree-nav-icon">&#128202;</span><span>EDA &amp; Insights</span></a>'
        f'<a href="/historical_analysis" target="_parent" class="gree-nav-item"><span class="gree-nav-icon">&#128200;</span><span>Historical Analysis</span></a>'
        f'<a href="/guide" target="_parent" class="gree-nav-item"><span class="gree-nav-icon">&#128214;</span><span>Guide</span></a>'
        f'</nav>'
    )

    components.html(
        f"""<script>
        (function() {{
            var doc = window.parent.document;

            // Inject font
            if (!doc.getElementById('gree-font')) {{
                var lnk = doc.createElement('link');
                lnk.id = 'gree-font';
                lnk.rel = 'stylesheet';
                lnk.href = {json.dumps(FONT_URL)};
                doc.head.appendChild(lnk);
            }}

            // Inject / update CSS
            var style = doc.getElementById('gree-styles');
            if (!style) {{
                style = doc.createElement('style');
                style.id = 'gree-styles';
                doc.head.appendChild(style);
            }}
            style.textContent = {json.dumps(css)};

            // Inject / update navbar HTML
            var old = doc.getElementById('gree-navbar');
            if (old) old.remove();
            var el = doc.createElement('div');
            el.id = 'gree-navbar';
            el.innerHTML = {json.dumps(navbar_html)};
            doc.body.prepend(el);

            // Hamburger toggle
            el.querySelector('.gree-hamburger').addEventListener('click', function() {{
                var sidebar = doc.querySelector('.gree-nav-sidebar');
                var main = doc.querySelector('[data-testid="stAppViewContainer"] > .main');
                var collapsed = sidebar.offsetWidth < 100;
                var w = collapsed ? '220px' : '60px';
                sidebar.style.width = w;
                if (main) main.style.marginLeft = w;
            }});

        }})();
        </script>""",
        height=0,
        scrolling=False,
    )

# ═════════════════════════════════════════════
# Main Theme Injection
# ═════════════════════════════════════════════
def inject_theme():
    """Inject adaptive theme CSS"""
    init_session()
    colors = get_theme_colors()
    
    css_style = textwrap.dedent(f"""<link href="{FONT_URL}" rel="stylesheet"><style>
    /* TRIK FADE-IN: Sembunyikan semuanya sebentar, lalu munculkan setelah CSS kita siap */
    [data-testid="stAppViewContainer"] {{
        animation: fadeInLayout 0.5s ease-in-out forwards;
    }}
    
    @keyframes fadeInLayout {{
        0% {{ opacity: 0; visibility: hidden; }}
        70% {{ opacity: 0; visibility: hidden; }} 
        100% {{ opacity: 1; visibility: visible; }}
    }}

    /* Sembunyikan bawaan Streamlit secepat mungkin */
    [data-testid="stSidebar"], [data-testid="stHeader"] {{
        display: none !important;
    }}

    :root {{
        --teal:   #00d4aa;
        --red:    #f04b64;
        --gold:   #f0b429;
        --blue:   #4d9fff;
        --violet: #a78bfa;
    }}

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background-color: {colors['bg_primary']} !important;
        color: {colors['txt1']} !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: all 0.3s ease;
    }}

    .block-container {{
        max-width: 1200px !important;
        padding-top: 1rem !important;
    }}

    #MainMenu, footer, [data-testid="stDecoration"] {{ 
        visibility: hidden; 
        display: none;
    }}

    h1, h2, h3 {{
        font-family: 'Syne', sans-serif !important;
        color: {colors['txt1']} !important;
        letter-spacing: -0.02em;
    }}

    p, label {{
        color: {colors['txt2']} !important;
    }}

    hr {{
        border: none;
        border-top: 1px solid {colors['border_light']} !important;
        margin: 1.5rem 0;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, var(--teal) 0%, #009e80 100%) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s !important;
        box-shadow: 0 0 20px rgba(0,212,170,0.18);
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 0 32px rgba(0,212,170,0.35) !important;
    }}

    [data-testid="stMetric"] {{
        background: {colors['bg_card']} !important;
        border: 1px solid {colors['border_light']} !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-3px);
    }}
    [data-testid="stMetricLabel"] > div {{
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {colors['txt2']} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: {colors['txt1']} !important;
    }}

    [data-testid="stSelectbox"] > div > div,
    [data-testid="stRadio"] > div {{
        background: {colors['bg_card']} !important;
        border: 1px solid {colors['border_light']} !important;
        border-radius: 8px !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        background: {colors['bg_surface']} !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 7px !important;
        color: {colors['txt2']} !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }}
    .stTabs [aria-selected="true"] {{
        background: {colors['bg_elevated']} !important;
        color: var(--teal) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }}

    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {colors['bg_primary']}; }}
    ::-webkit-scrollbar-thumb {{ 
        background: {colors['txt3']}; 
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--teal); }}
    </style>
    """)
    st.markdown(css_style, unsafe_allow_html=True)


def get_plotly_layout():
    """Get Plotly layout matching current theme"""
    colors = get_theme_colors()
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=colors['plot_bg'],
        font=dict(family="DM Sans, sans-serif", color=colors['txt2'], size=11),
        xaxis=dict(showgrid=True, gridcolor=colors['plot_grid'], linecolor=colors['border']),
        yaxis=dict(showgrid=True, gridcolor=colors['plot_grid'], linecolor=colors['border']),
        hovermode="x unified",
    )

def page_header(title: str, subtitle: str = ""):
    colors = get_theme_colors()
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;
        color:{colors['txt3']};margin-bottom:0.3rem;">{subtitle}</div>
        <h1 style="font-size:1.9rem;font-weight:800;margin:0;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

def section_label(text: str):
    colors = get_theme_colors()
    st.markdown(f"""
    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;
    color:{colors['txt3']};margin:1.5rem 0 0.8rem 0;">{text}</div>
    """, unsafe_allow_html=True)