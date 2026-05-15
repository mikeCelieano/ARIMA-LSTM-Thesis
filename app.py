import streamlit as st

st.set_page_config(
    page_title="BAM Board | Forex Prediction",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        /* Sembunyikan UI Bawaan Streamlit secepat mungkin */
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

        /* 🎬 TIRAI TRANSISI (CURTAIN OVERLAY) */
        #gree-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #070b12; /* Sama dengan warna bg gelapmu */
            z-index: 9999999;
            pointer-events: none; /* Agar tidak memblokir klik */
            
            /* Animasi Fade-In: Saat halaman baru dibuka, tirai perlahan menghilang */
            animation: fadeOutCurtain 0.7s cubic-bezier(0.4, 0, 0.2, 1) forwards;
            animation-delay: 0.15s; /* Tunggu komponen Streamlit ter-render sempurna di belakang layar */
        }

        @keyframes fadeOutCurtain {
            0% { opacity: 1; visibility: visible; }
            100% { opacity: 0; visibility: hidden; }
        }
    </style>
    
    <div id="gree-overlay"></div>
""", unsafe_allow_html=True)

home_page = st.Page("_pages/home.py", title="Home", icon="🏠", url_path="home")
guide_page = st.Page("_pages/guide.py", title="Guide", icon="💻", url_path="guide")
prediction_page = st.Page("_pages/prediction.py", title="Prediction", icon="📈", url_path="prediction")
eda_page = st.Page("_pages/eda.py", title="EDA & Insights", icon="📊", url_path="eda")

pg = st.navigation({
    "Main Menu": [home_page, guide_page],
    "Analysis & Prediction": [prediction_page, eda_page]
})

pg.run()