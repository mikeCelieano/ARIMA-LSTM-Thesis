import streamlit as st

st.set_page_config(
    page_title="BAM Board | Forex Prediction",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        /* Sembunyikan UI Bawaan Streamlit */
        [data-testid="stHeader"], 
        [data-testid="stSidebar"], 
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        [data-testid="stAppViewContainer"] > .main {
            margin-top: 60px !important; 
            background-color: #070b12 !important; 
        }
    </style>
""", unsafe_allow_html=True)

def gateway():
    st.switch_page("_pages/home.py")
    
gateway_page = st.Page(gateway, title="Gateway", default=True)

home_page = st.Page("_pages/home.py", title="Home", icon="🏠", url_path="home")
guide_page = st.Page("_pages/guide.py", title="Guide", icon="💻", url_path="guide")
prediction_page = st.Page("_pages/prediction.py", title="Prediction", icon="📈", url_path="prediction")
eda_page = st.Page("_pages/eda.py", title="EDA & Insights", icon="📊", url_path="eda")
monitor_page = st.Page("_pages/monitor.py", title="System Monitor", icon="🖥️", url_path="monitor")

pg = st.navigation({
    "System": [gateway_page],
    "Main Menu": [home_page, guide_page],
    "Analysis & Prediction": [prediction_page, eda_page],
    "Server Status": [monitor_page]
})

pg.run()