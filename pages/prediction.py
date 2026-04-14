import streamlit as st
import numpy as np
import pandas as pd
from datetime import timedelta

from utils.data_loader import df_map, custom_bd
from utils.features import prepare_inference_data
from utils.metrics import get_dynamic_metrics
from models.model_manager import ModelManager
from utils.visualizations import plot_forex, display_side_by_side_metrics, choose_sidebar_plot_range

if 'predicted' not in st.session_state: st.session_state.predicted = False
if 'current_currency' not in st.session_state: st.session_state.current_currency = None

st.sidebar.markdown("### 💱 Pilih Mata Uang")
currency = st.sidebar.radio("Pilih satu yang ingin dilihat prediksinya", ["USD/IDR", "EUR/IDR", "GBP/IDR"])

st.sidebar.markdown("### ⚙️ Pilih Model Utama")
selected_model = st.sidebar.selectbox(
    "Pilih model untuk visualisasi grafik:", 
    ["ARIMA-LSTM Hybrid", "ARIMA", "LSTM"]
)

st.sidebar.markdown("### 🧠 Mode Model")
model_mode = st.sidebar.radio(
    "Pilih jenis model:",
    ["Tuning", "Non-Tuning"]
)

# ⬇️ TARO DI SINI
mode_map = {
    "Tuning": "tuned",
    "Non-Tuning": "baseline"
}

n_days = choose_sidebar_plot_range()

if st.session_state.current_currency != currency:
    st.session_state.predicted = False
    st.session_state.current_currency = currency

# Ambil data terbaru untuk UI
df = df_map[currency]()
last_date = df.index[-1]
future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=1, freq=custom_bd)

st.sidebar.markdown("### 🗓 Tanggal Penutupan Terakhir")
st.sidebar.write(last_date.strftime('%d %B %Y'))
st.sidebar.markdown("### 🗓 Tanggal yang Akan Diprediksi")
st.sidebar.write(future_dates[0].strftime('%d %B %Y'))

st.header("Prediksi & Evaluasi Model Valuta Asing")
st.write("---")

# --- TOMBOL PREDIKSI ---
if st.sidebar.button("🔮 Mulai Analisis"):
    with st.spinner(f"Memuat model {currency} dan mengeksekusi prediksi..."):
        
        try:
            # 1. Siapkan data H-1 untuk dilempar ke model
            df_inference, exog_inference = prepare_inference_data(df)
            
            # 2. Panggil Model Manager (Memuat file .pkl dan .keras)
            manager = ModelManager(currency, mode=mode_map[model_mode])
            is_loaded = manager.load_all_models()
            
            if not is_loaded:
                st.error("⚠️ Model belum ditemukan! Pastikan proses training awal sudah selesai.")
            else:
                # 3. Prediksi dari ketiga model secara bersamaan
                all_results = manager.predict_all(df_inference, exog_inference)
                
                # Simpan ke Session State
                st.session_state.all_results = all_results
                st.session_state.inference_df = df_inference
                st.session_state.predicted = True
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")

# --- TAMPILAN HASIL ---
if not st.session_state.predicted:
    st.info("Klik tombol '🔮 Mulai Analisis' pada sidebar untuk memuat prediksi dari seluruh model.")
else:
    active_result = st.session_state.all_results[selected_model]
    
    # 1. Tampilkan Metrik Prediksi H+1 Model Terpilih
    st.subheader(f"📈 Hasil Prediksi Detail: {selected_model}")
    col1, col2, col3 = st.columns(3)
    
    last_price = st.session_state.inference_df['Close Price'].iloc[-1]
    pred_price = active_result['next_price']
    selisih = pred_price - last_price
    persen = (selisih / last_price) * 100
    
    col1.metric(label=f"Prediksi ({future_dates[0].strftime('%d-%m-%Y')})", 
                value=f"Rp {pred_price:,.2f}", 
                delta=f"Rp {selisih:,.2f} ({persen:.2f}%)")
    col2.metric(label="Batas Atas (95% CI)", value=f"Rp {active_result['upper_ci']:,.2f}")
    col3.metric(label="Batas Bawah (95% CI)", value=f"Rp {active_result['lower_ci']:,.2f}")
    
    # 2. Tampilkan Plot Grafik
    st.write("")
    
    # Menyesuaikan format dataframe hasil prediksi untuk plot_forex
    forecast_df_format = pd.DataFrame({
        "Date": future_dates,
        "Forecast": [pred_price],
        "Lower CI": [active_result['lower_ci']],
        "Upper CI": [active_result['upper_ci']]
    })
    
    plot_forex(df, forecast_df_format, 1, n_days=n_days)
    
    # ==========================================
    # 3. MENAMPILKAN EVALUASI METRIK SECARA DINAMIS
    # ==========================================
    st.markdown("---")
    st.subheader("📊 Evaluasi Performa Model (Testing Set 30 Hari)")
    
    with st.spinner("⏳ Menghitung metrik evaluasi dinamis... (Hanya memakan waktu agak lama pada klik pertama)"):
        # Tarik data utuh
        df_inf, exog_inf = prepare_inference_data(df)
        
        # Eksekusi caching perhitungan backtest
        eval_metrics_dynamic = get_dynamic_metrics(
            currency,
            df_inf,
            exog_inf,
            mode=mode_map[model_mode],
            model_name=selected_model,
            test_days=30
        )
        
        # Tampilkan tabel komparasi
        if eval_metrics_dynamic:
            # display_side_by_side_metrics(eval_metrics_dynamic)
            metrics = eval_metrics_dynamic[selected_model]

            st.write("")
            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                label="MAE",
                value=f"{metrics['MAE']:.4f}"
            )

            col2.metric(
                label="RMSE",
                value=f"{metrics['RMSE']:.4f}"
            )

            col3.metric(
                label="MAPE (%)",
                value=f"{metrics['MAPE']:.2f}%"
            )

            col4.metric(
                label="CI Coverage",
                value=f"{metrics['CI Coverage']:.2f}%"
            )
        else:
            st.error("Gagal memuat metrik evaluasi. Pastikan model sudah di-training.")