import streamlit as st
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

st.title("💻 Panduan Penggunaan")
st.divider()

st.header("📈 Cara Melihat Prediksi")
st.write("1. Pilih menu **Mulai Prediksi** di sidebar.")
st.write("2. Pilih mata uang dan model yang ingin digunakan.")
st.write("3. Klik tombol **🔮 Mulai Analisis**.")

st.divider()

st.header("📊 Cara Melihat Analisis Historis")
st.write("1. Pilih menu **Analisis Historis** di sidebar.")
st.write("2. Pilih mata uang yang ingin dianalisis.")
st.write("3. Klik tombol **📊 Tampilkan Grafik**.")