import streamlit as st
import pandas as pd
from utils.data_loader import df_map
from utils.visualizations import plot_macd, plot_rsi, choose_plot_range
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

st.header("Analisis Historis")

currency = st.radio("Pilih Mata Uang", ["USD/IDR", "EUR/IDR", "GBP/IDR"], horizontal=True)

if 'current_df' not in st.session_state or st.session_state.get('last_currency') != currency:
    df = df_map[currency]()
    st.session_state.current_df = df
    st.session_state.last_currency = currency
else:
    df = st.session_state.current_df

if st.button("📊 Tampilkan Grafik"):
    st.session_state.show_analysis = True

if st.session_state.get('show_analysis'):
    n_days = choose_plot_range()
    tab1, tab2 = st.tabs(["MACD", "RSI"])
    with tab1:
        plot_macd(df, n_days)
    with tab2:
        plot_rsi(df, n_days)