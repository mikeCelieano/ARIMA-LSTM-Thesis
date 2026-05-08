import streamlit as st
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

st.markdown("<h1>💸 Gree: Sistem Prediksi Harga Penutupan Valuta Asing</h1>", unsafe_allow_html=True)
st.divider()

st.subheader("Tentang Gree")
st.markdown("""
    Gree adalah sistem yang dirancang untuk memberikan **informasi prediktif** mengenai 
    **harga penutupan valuta asing terhadap Rupiah (IDR)**.
    
    Nilai tukar yang didukung:
    - **USD/IDR**
    - **EUR/IDR**
    - **GBP/IDR**
""")

st.write("")
st.subheader("Fitur Utama")
st.markdown("##### 📈 Prediksi Harga Penutupan")
st.markdown("""
    Prediksi harga penutupan 1 hari ke depan menggunakan model ARIMA, LSTM, dan Hybrid.
""")

st.write("")
st.subheader("Sumber Data")
st.markdown("""
    **1. Data Harga Forex**
    - Sumber: *Investing.com* 🔗 https://www.investing.com/
    
    **2. Variabel Eksternal**
    - Inflasi & BI Rate
    - Sumber: *Bank Indonesia* 🔗 https://www.bi.go.id/
""")

st.divider()
st.caption(
    "⚠️ Sistem ini dikembangkan sebagai bagian dari tugas akhir akademik. "
    "Hasil prediksi bersifat informatif dan bukan rekomendasi investasi."
)