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
    """Inject navbar via components.html() - sidebar slides in/out on hamburger click."""
    init_session()
    colors = get_theme_colors()

    controls_html = ""
    if show_prediction_controls:
        controls_html = (
            f'<div class="gree-prediction-controls">'
            f'<span class="gree-control-badge">{currency}</span>'
            f'<span class="gree-control-badge">{model}</span>'
            f'<span class="gree-control-badge">{mode}</span>'
            f'</div>'
        )

    css = (
        # Top bar
        f'.gree-top-bar{{position:fixed;top:0;left:0;right:0;height:60px;'
        f'background:{colors["bg_card"]};border-bottom:1px solid {colors["border_light"]};'
        f'display:flex;align-items:center;justify-content:space-between;padding:0 1.5rem;'
        f'z-index:99999;backdrop-filter:blur(10px);box-shadow:0 2px 8px rgba(0,0,0,.06);'
        f'font-family:"DM Sans",sans-serif;box-sizing:border-box}}'
        f'.gree-top-bar-left{{display:flex;align-items:center;gap:1rem}}'
        f'.gree-hamburger{{font-size:1.6rem;cursor:pointer;color:{colors["txt2"]};'
        f'user-select:none;transition:color .2s;padding:.3rem .5rem;border-radius:6px;'
        f'display:inline-flex;align-items:center;justify-content:center}}'
        f'.gree-hamburger:hover{{color:#00d4aa;background:{colors["bg_surface"]}}}'
        f'.gree-brand{{font-family:"Syne",sans-serif;font-size:1.3rem;font-weight:800;'
        f'color:{colors["txt1"]};letter-spacing:-.02em}}'
        f'.gree-prediction-controls{{display:flex;gap:.6rem;align-items:center}}'
        f'.gree-control-badge{{background:{colors["bg_surface"]};border:1px solid {colors["border"]};'
        f'border-radius:6px;padding:.35rem .75rem;font-size:.78rem;color:{colors["txt2"]};font-weight:500}}'

        # Sidebar
        f'.gree-nav-sidebar{{position:fixed;left:0;top:60px;bottom:0;width:240px;'
        f'background:{colors["bg_surface"]};border-right:1px solid {colors["border_light"]};'
        f'transform:translateX(-100%);transition:transform .3s cubic-bezier(.4,0,.2,1);'
        f'overflow-y:auto;overflow-x:hidden;z-index:99998;white-space:nowrap;'
        f'box-shadow:4px 0 20px rgba(0,0,0,0.3)}}'
        f'.gree-nav-sidebar.is-open{{transform:translateX(0)}}'

        # Backdrop
        f'.gree-backdrop{{position:fixed;top:60px;left:0;right:0;bottom:0;'
        f'background:rgba(0,0,0,0.4);opacity:0;visibility:hidden;'
        f'transition:opacity .3s, visibility .3s;z-index:99997}}'
        f'.gree-backdrop.is-open{{opacity:1;visibility:visible}}'

        # Nav items
        f'.gree-nav-item{{display:flex;align-items:center;gap:1rem;padding:.9rem 1.4rem;'
        f'color:{colors["txt2"]};text-decoration:none;font-family:"DM Sans",sans-serif;'
        f'font-size:0.95rem;transition:all 0.2s;border-left:3px solid transparent;cursor:pointer}}'
        f'.gree-nav-item:hover{{background:{colors["bg_elevated"]};color:#00d4aa;border-left-color:#00d4aa}}'
        f'.gree-nav-icon{{font-size:1.3rem;min-width:24px;text-align:center}}'

        f'[data-testid="stAppViewContainer"]>.main{{margin-top:60px!important;padding:1.5rem 2rem!important}}'

        f'@media (max-width: 768px) {{'
        f'  .gree-prediction-controls {{ display: none !important; }}'
        f'  .gree-brand {{ font-size: 1.1rem; }}'
        f'  .gree-top-bar {{ padding: 0 1rem; }}'
        f'  [data-testid="stAppViewContainer"]>.main {{ padding: 1rem 1rem !important; }}'
        f'}}'
    )

    navbar_html = (
        f'<div class="gree-top-bar">'
        f'<div class="gree-top-bar-left">'
        f'<span class="gree-hamburger" id="gree-hamburger-btn">&#9776;</span>'
        f'<span class="gree-brand">&#129689; BAM Board</span>'
        f'{controls_html}'
        f'</div>'
        f'</div>'
        f'<div class="gree-backdrop" id="gree-backdrop"></div>'
        f'<nav class="gree-nav-sidebar" id="gree-sidebar">'
        f'<a href="#" data-target="home" class="gree-nav-item"><span class="gree-nav-icon">&#127968;</span><span>Home</span></a>'
        f'<a href="#" data-target="prediction" class="gree-nav-item"><span class="gree-nav-icon">&#128302;</span><span>Prediction</span></a>'
        f'<a href="#" data-target="eda" class="gree-nav-item"><span class="gree-nav-icon">&#128202;</span><span>EDA &amp; Insights</span></a>'
        f'<a href="#" data-target="guide" class="gree-nav-item"><span class="gree-nav-icon">&#128214;</span><span>Guide</span></a>'
        f'</nav>'
    )

    components.html(
        f"""<script>
        (function() {{
            var doc = window.parent.document;

            if (!doc.getElementById('gree-font')) {{
                var lnk = doc.createElement('link');
                lnk.id = 'gree-font'; lnk.rel = 'stylesheet'; lnk.href = {json.dumps(FONT_URL)};
                doc.head.appendChild(lnk);
            }}

            var style = doc.getElementById('gree-styles');
            if (!style) {{
                style = doc.createElement('style'); style.id = 'gree-styles';
                doc.head.appendChild(style);
            }}
            style.textContent = {json.dumps(css)};

            var old = doc.getElementById('gree-navbar');
            if (old) old.remove();

            var el = doc.createElement('div');
            el.id = 'gree-navbar';
            el.innerHTML = {json.dumps(navbar_html)};
            doc.body.prepend(el);

            var btn = doc.getElementById('gree-hamburger-btn');
            var sidebar = doc.getElementById('gree-sidebar');
            var backdrop = doc.getElementById('gree-backdrop');

            function closeSidebar() {{
                sidebar.classList.remove('is-open');
                backdrop.classList.remove('is-open');
                try {{ window.parent.localStorage.setItem('gree-sidebar-open', '0'); }} catch(e) {{}}
            }}

            btn.addEventListener('click', function(e) {{
                e.preventDefault(); e.stopPropagation();
                var isOpen = sidebar.classList.toggle('is-open');
                backdrop.classList.toggle('is-open', isOpen);
                try {{ window.parent.localStorage.setItem('gree-sidebar-open', isOpen ? '1' : '0'); }} catch(e) {{}}
            }});

            backdrop.addEventListener('click', closeSidebar);

            sidebar.querySelectorAll('.gree-nav-item').forEach(function(link) {{
                link.addEventListener('click', function(e) {{
                    e.preventDefault(); e.stopPropagation();
                    closeSidebar();

                    var targetPage = this.getAttribute('data-target');
                    var parentWin = window.parent;
                    var parentDoc = parentWin.document;
                    
                    var nativeLinks = parentDoc.querySelectorAll('[data-testid="stSidebarNavLink"]');
                    var clicked = false;
                    
                    for (var i = 0; i < nativeLinks.length; i++) {{
                        var a = nativeLinks[i];
                        var href = a.getAttribute('href') || '';
                        
                        if (href.endsWith('/' + targetPage)) {{
                            a.click(); // Klik tombol aslinya
                            clicked = true;
                            break;
                        }}
                    }}
                    
                    if (!clicked) {{
                        parentWin.location.assign('/' + targetPage);
                    }}
                }});
            }});
        }})();
        </script>""",
        height=1,
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
    
    [data-testid="stAppViewContainer"] {{
        animation: fadeInLayout 0.5s ease-in-out forwards;
    }}
    @keyframes fadeInLayout {{
        0% {{ opacity: 0; visibility: hidden; }}
        70% {{ opacity: 0; visibility: hidden; }} 
        100% {{ opacity: 1; visibility: visible; }}
    }}
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
        max-width: 1400px !important; /* Diperlebar sedikit agar bagus di monitor/TV */
        padding-top: 1rem !important;
    }}

    /* PERUBAHAN 3: Tipografi Karet (Responsive Typography) */
    h1, h2, h3 {{
        font-family: 'Syne', sans-serif !important;
        color: {colors['txt1']} !important;
        letter-spacing: -0.02em;
    }}
    h1 {{ font-size: clamp(1.8rem, 4vw, 2.8rem) !important; }}
    h2 {{ font-size: clamp(1.4rem, 3vw, 2.2rem) !important; }}
    h3 {{ font-size: clamp(1.1rem, 2vw, 1.5rem) !important; }}

    p, label {{ color: {colors['txt2']} !important; }}

    
    /* PERUBAHAN 4: Perbaikan Metrik di Layar Kecil */
    [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: clamp(1rem, 2vw, 1.4rem) !important; /* Nilai rupiah mengecil di HP */
        font-weight: 600 !important;
        color: {colors['txt1']} !important;
        word-wrap: break-word; /* Mencegah angka panjang tumpah dari kotak */
    }}
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