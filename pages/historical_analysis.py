import streamlit as st
import pandas as pd
from utils.data_loader import df_map
from utils.visualizations import plot_macd, plot_rsi, choose_plot_range

st.header("Analisis Historis dengan Indikator Teknikal")

st.markdown("### Pilih Mata Uang untuk Dianalisis")
currency = st.radio("Mata Uang", ["USD/IDR", "EUR/IDR", "GBP/IDR"], horizontal=True)

# --- FIX: Inisialisasi data jika belum ada di session state ---
if 'current_df' not in st.session_state or st.session_state.get('last_currency') != currency:
    # Memuat data secara mandiri berdasarkan pilihan radio button
    df = df_map[currency]()
    st.session_state.current_df = df
    st.session_state.last_currency = currency
else:
    df = st.session_state.current_df

if st.button("📊 Lihat Analisis"):
    st.session_state.show_analysis = True

if st.session_state.get('show_analysis'):
    st.divider()
    
    # Memilih rentang waktu visualisasi
    n_days = choose_plot_range()
    
    tab1, tab2 = st.tabs(["MACD", "RSI"])
    
    with tab1:
        # Menggunakan df yang sudah dipastikan ada
        plot_macd(df, n_days)
        
    with tab2:
        plot_rsi(df, n_days)