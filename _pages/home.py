import streamlit as st
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

st.markdown("<h1>🪙 BAM Board: Forex Closing Price Prediction System</h1>", unsafe_allow_html=True)
st.divider()

st.subheader("About BAM Board")
st.markdown("""
    BAM Board is a system designed to provide **predictive information** about
    **forex closing prices against the Indonesian Rupiah (IDR)**.

    Supported exchange rates:
    - **USD/IDR**
    - **EUR/IDR**
    - **GBP/IDR**
""")

st.write("")
st.subheader("Key Features")
st.markdown("##### 📈 Closing Price Prediction")
st.markdown("""
    Forecasts the next-day closing price using ARIMA, LSTM, and Hybrid models.
""")

st.write("")
st.subheader("Data Sources")
st.markdown("""
    **1. Forex Price Data**
    - Source: *Investing.com* 🔗 https://www.investing.com/

    **2. External Variables**
    - Inflation & BI Rate
    - Source: *Bank Indonesia* 🔗 https://www.bi.go.id/
""")

st.divider()
st.caption(
    "⚠️ This system was developed as part of an academic thesis. "
    "Predictions are for informational purposes only and do not constitute investment advice."
)
