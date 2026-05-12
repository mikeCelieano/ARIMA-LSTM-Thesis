import streamlit as st
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

st.title("💻 User Guide")
st.divider()

st.header("📈 How to View Predictions")
st.write("1. Select **Prediction** from the navigation menu.")
st.write("2. Choose a currency pair and model.")
st.write("3. The prediction runs automatically when settings change.")

st.divider()

st.header("📊 How to View Historical Analysis")
st.write("1. Select **Historical Analysis** from the navigation menu.")
st.write("2. Choose the currency pair to analyse.")
st.write("3. Click **📊 Show Chart**.")
