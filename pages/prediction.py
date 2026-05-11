import streamlit as st
import pandas as pd
from datetime import timedelta

from utils.data_loader import df_map, custom_bd
from utils.features import prepare_inference_data
from utils.metrics import get_dynamic_metrics
from models.model_manager import ModelManager
from utils.visualizations import plot_forex_interactive, choose_sidebar_plot_range, _INTERACTIVE_CFG
from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()

if 'predicted' not in st.session_state:
    st.session_state.predicted = False
if 'last_settings' not in st.session_state:
    st.session_state.last_settings = {}

# ─────────────────────────────────────────────
# Sidebar Controls
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    currency = st.selectbox("💱 Currency", ["USD/IDR", "EUR/IDR", "GBP/IDR"])

with col2:
    selected_model = st.selectbox("⚙️ Model", ["ARIMA-LSTM Hybrid", "ARIMA", "LSTM"])

with col3:
    model_mode = st.selectbox("🧠 Mode", ["Tuning", "Non-Tuning"])

with col4:
    n_days_options = {"7D": 7, "1M": 30, "3M": 90, "1Y": 365}
    n_days_label = st.selectbox("📅 Range", list(n_days_options.keys()), index=1)
    n_days = n_days_options[n_days_label]

# Add navbar
render_hybrid_navbar(
    show_prediction_controls=True,
    currency=currency,
    model=selected_model,
    mode=model_mode
)

# ─────────────────────────────────────────────
# AUTO-REFRESH LOGIC (Goal 3)
# ─────────────────────────────────────────────
current_settings = {
    'currency': currency,
    'model': selected_model,
    'mode': model_mode,
}

# Detect if settings changed
settings_changed = (st.session_state.last_settings != current_settings)

if settings_changed:
    st.session_state.last_settings = current_settings
    st.session_state.predicted = False  # Trigger re-prediction

# Load data
df = df_map[currency]()
last_date = df.index[-1]
future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=1, freq=custom_bd)

st.sidebar.markdown(f"**Latest Data:** {last_date.strftime('%d %b %Y')}")
st.sidebar.markdown(f"**Prediction Target:** {future_dates[0].strftime('%d %b %Y')}")

# ─────────────────────────────────────────────
# AUTO-RUN PREDICTION
# ─────────────────────────────────────────────
if not st.session_state.predicted or settings_changed:
    with st.spinner("⏳ Running prediction..."):
        try:
            df_inf, exog_inf = prepare_inference_data(df)
            manager = ModelManager(currency, mode=model_mode)
            
            if manager.load_all_models():
                st.session_state.all_results = manager.predict_all(df_inf, exog_inf)
                st.session_state.inference_df = df_inf
                st.session_state.exog_inf = exog_inf
                st.session_state.predicted = True
            else:
                st.error("⚠️ Model not found!")
                st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

# ─────────────────────────────────────────────
# Main Display
# ─────────────────────────────────────────────
st.header(f"{currency} Prediction")

res = st.session_state.all_results[selected_model]
df_inf = st.session_state.inference_df
exog_inf = st.session_state.exog_inf
last_price = df_inf['Close Price'].iloc[-1]
pred_price = res['next_price']
delta = pred_price - last_price
pct = (delta / last_price) * 100

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Prediction", f"Rp {pred_price:,.2f}", f"{delta:+,.2f} ({pct:+.2f}%)")
col2.metric("Upper CI", f"Rp {res['upper_ci']:,.2f}")
col3.metric("Lower CI", f"Rp {res['lower_ci']:,.2f}")

# Interactive Chart (Goal 4)
fig = plot_forex_interactive(df_inf, res, currency, n_days=n_days)
st.plotly_chart(fig, use_container_width=True, config=_INTERACTIVE_CFG)

# Metrics evaluation
st.markdown("---")
st.subheader("📊 Model Evaluation (Last 30 Days)")

with st.spinner("Calculating metrics..."):
    try:
        eval_res = get_dynamic_metrics(currency, df_inf, exog_inf, model_mode, selected_model, 30)
        if eval_res:
            m = eval_res[selected_model]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("MAE", f"{m['MAE']:.4f}")
            c2.metric("RMSE", f"{m['RMSE']:.4f}")
            c3.metric("MAPE", f"{m['MAPE']:.2f}%")
            c4.metric("CI Coverage", f"{m['CI Coverage']:.0f}%")
    except Exception as e:
        st.warning(f"Failed to calculate metrics: {e}")
