import streamlit as st

st.set_page_config(
    page_title="Sistem Prediksi Forex",
    page_icon="💸",
    layout="centered"
)

# Sesuaikan string path dengan nama file aslimu di dalam folder pages/
beranda = st.Page("pages/home.py", title="Beranda", icon="🏠")
panduan = st.Page("pages/guide.py", title="Panduan", icon="📖")
prediksi = st.Page("pages/prediction.py", title="Mulai Prediksi", icon="🔮")
analisis = st.Page("pages/historical_analysis.py", title="Analisis Historis", icon="📈")

pg = st.navigation([beranda, panduan, prediksi, analisis])
pg.run()