import streamlit as st

# 1. WAJIB: Perintah Streamlit pertama di file entry point
st.set_page_config(
    page_title="Gree | Forex Prediction",
    page_icon="💸",
    layout="wide"
)

# 2. Definisi Halaman (Atur judul dan ikon di sini)
home_page = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
guide_page = st.Page("pages/guide.py", title="Panduan", icon="💻")
historical_page = st.Page("pages/historical_analysis.py", title="Analisis Historis", icon="📊")
prediction_page = st.Page("pages/prediction.py", title="Prediksi", icon="📈")
eda_page = st.Page("pages/eda.py", title="EDA & Insights", icon="📊")
# 3. Navigasi
pg = st.navigation({
    "Menu Utama": [home_page, guide_page],
    "Analisis & Prediksi": [historical_page, prediction_page, eda_page]
})

pg.run()