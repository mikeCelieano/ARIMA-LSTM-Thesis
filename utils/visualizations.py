import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from datetime import timedelta
from utils.data_loader import custom_bd
from utils.indicators import calculate_macd, calculate_rsi

def plot_forex(df, df_forecast, step, n_days):
    start_date = df.index.max() - pd.Timedelta(days=n_days)
    df_filtered = df.loc[df.index >= start_date]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["Close Price"], mode="lines", name="Historis", line=dict(color="blue", width=2)))
    fig.add_trace(go.Scatter(
        x=list(df_forecast["Date"]) + list(df_forecast["Date"][::-1]),
        y=list(df_forecast["Upper CI"]) + list(df_forecast["Lower CI"][::-1]),
        fill='toself', fillcolor='rgba(255,0,0,0.2)', line=dict(color='rgba(255,100,100,0.5)', width=1),
        name="Confidence Interval (95%)", hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=df_forecast["Date"], y=df_forecast["Forecast"], mode="lines+markers+text", name="Hasil Prediksi",
        line=dict(color="red", width=2, dash="dash"), marker=dict(color="red", size=6),
        textposition="top center", hovertemplate="Tanggal: %{x}<br>Prediksi: Rp %{y:,.3f}<extra></extra>"
    ))
    
    fig.update_layout(template="plotly_white", title={'text': "Visualisasi Data Historis dan Hasil Prediksi", 'x': 0.5}, hovermode="x unified", height=450)
    st.plotly_chart(fig, use_container_width=True)

def display_comparison_table(backtest_df, currency):
    st.header("📊 Evaluasi Performa Model")
    display_df = backtest_df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%d-%m-%Y')
    display_df['Actual'] = display_df['Actual'].apply(lambda x: f"Rp {x:,.2f}")
    display_df['Predicted'] = display_df['Predicted'].apply(lambda x: f"Rp {x:,.2f}")
    display_df['Lower_CI'] = display_df['Lower_CI'].apply(lambda x: f"Rp {x:,.2f}")
    display_df['Upper_CI'] = display_df['Upper_CI'].apply(lambda x: f"Rp {x:,.2f}")
    display_df['Error'] = display_df['Error'].apply(lambda x: f"Rp {x:,.2f}")
    display_df['Error_Pct'] = display_df['Error_Pct'].apply(lambda x: f"{x:,.2f}%")
    display_df['Within_CI'] = display_df['Within_CI'].apply(lambda x: "✅ Ya" if x else "❌ Tidak")
    
    display_df.columns = ['Tanggal', 'Harga Aktual', 'Hasil Prediksi', 'Batas Bawah (95%)', 'Batas Atas (95%)', 'Dalam CI?', 'Selisih', 'Selisih (%)']
    st.dataframe(display_df[['Tanggal', 'Harga Aktual', 'Hasil Prediksi', 'Batas Bawah (95%)', 'Batas Atas (95%)', 'Dalam CI?', 'Selisih', 'Selisih (%)']], use_container_width=True, hide_index=True)
    
    mae = backtest_df['Error'].abs().mean()
    mape = backtest_df['Error_Pct'].abs().mean()
    rmse = np.sqrt((backtest_df['Error'] ** 2).mean())
    ci_coverage = (backtest_df['Within_CI'].sum() / len(backtest_df)) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MAE", f"Rp {mae:,.2f}")
    col2.metric("MAPE", f"{mape:.2f}%")
    col3.metric("RMSE", f"Rp {rmse:,.2f}")
    col4.metric("CI Coverage", f"{ci_coverage:.0f}%")
    return mae, mape, rmse, ci_coverage

def plot_comparison(backtest_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(backtest_df['Date']) + list(backtest_df['Date'][::-1]), y=list(backtest_df['Upper_CI']) + list(backtest_df['Lower_CI'][::-1]), fill='toself', fillcolor='rgba(255,0,0,0.2)', line=dict(color='rgba(255,0,0,0)'), name='Confidence Interval (95%)', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=backtest_df['Date'], y=backtest_df['Actual'], mode='lines+markers', name='Harga Aktual', line=dict(color='blue', width=2)))
    fig.add_trace(go.Scatter(x=backtest_df['Date'], y=backtest_df['Predicted'], mode='lines+markers', name='Hasil Prediksi', line=dict(color='red', width=2, dash='dash')))
    fig.update_layout(template="plotly_white", title={'text': "Perbandingan Harga Aktual vs Prediksi Model", 'x': 0.5}, hovermode="x unified", height=400)
    st.plotly_chart(fig, use_container_width=True)

def plot_macd(df, n_days):
    start_date = df.index.max() - pd.Timedelta(days=n_days)
    df_macd = calculate_macd(df.loc[df.index >= start_date])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_macd.index, y=df_macd['MACD'], mode='lines', name='MACD', line=dict(color='blue', width=2)))
    fig.add_trace(go.Scatter(x=df_macd.index, y=df_macd['Signal'], mode='lines', name='Signal', line=dict(color='red', width=2)))
    colors = ['green' if val >= 0 else 'red' for val in df_macd['Histogram']]
    fig.add_trace(go.Bar(x=df_macd.index, y=df_macd['Histogram'], name='Histogram', marker_color=colors, opacity=0.5))
    fig.update_layout(template="plotly_white", title={'text': "MACD", 'x': 0.5}, hovermode="x unified", height=400)
    st.plotly_chart(fig, use_container_width=True)

def plot_rsi(df, n_days, period=14):
    start_date = df.index.max() - pd.Timedelta(days=n_days)
    df_rsi = calculate_rsi(df.loc[df.index >= start_date], period=period)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_rsi.index, y=df_rsi['RSI'], mode='lines', name='RSI', line=dict(color='purple', width=2), fill='tozeroy', fillcolor='rgba(128, 0, 128, 0.1)'))
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
    fig.update_layout(template="plotly_white", title={'text': f"RSI - Period {period}", 'x': 0.5}, hovermode="x unified", yaxis=dict(range=[0, 100]), height=400)
    st.plotly_chart(fig, use_container_width=True)

def display_prediction_results(results):
    st.header(f"📊 Prediksi Close Price {results['currency']}")
    st.metric(label=results['last_date'].strftime('%d-%m-%Y'), value=f"Rp {results['last_price']:,.2f}")
    col1, col2, col3 = st.columns(3)
    col1.metric(label=f"{results['future_dates'][0].strftime('%d-%m-%Y')}", value=f"Rp {results['next_price']:,.2f}", delta=f"Rp.{results['perubahan_prediksi']:,.2f} ({results['perubahan_persen']:,.2f}%)")
    col2.metric(label="Batas Atas (95%)", value=f"Rp {results['upper_ci']:,.2f}")
    col3.metric(label="Batas Bawah (95%)", value=f"Rp {results['lower_ci']:,.2f}")

# def choose_plot_range():
#     range_option = st.radio("Pilih rentang visualisasi", ["1 Minggu Terakhir", "2 Minggu Terakhir", "1 Bulan Terakhir", "3 Bulan Terakhir", "6 Bulan Terakhir", "1 Tahun Terakhir"], horizontal=True)
#     mapping = {"1 Minggu Terakhir": 7, "2 Minggu Terakhir": 14, "1 Bulan Terakhir": 30, "3 Bulan Terakhir": 90, "6 Bulan Terakhir": 180, "1 Tahun Terakhir": 365}
#     return mapping[range_option]

def choose_plot_range():
    options = [
        "1 Hari", "7 Hari", "1 Bulan", "3 Bulan", "5 Bulan", 
        "1 Tahun", "3 Tahun", "5 Tahun", "10 Tahun", "All Time"
    ]
    range_option = st.radio("Pilih rentang visualisasi", options, horizontal=True)
    
    mapping = {
        "1 Hari": 1, 
        "7 Hari": 7, 
        "1 Bulan": 30, 
        "3 Bulan": 90, 
        "5 Bulan": 150, 
        "1 Tahun": 365,
        "3 Tahun": 1095,   # 365 * 3
        "5 Tahun": 1825,   # 365 * 5
        "10 Tahun": 3650,  # 365 * 10
        "All Time": 99999  # Angka besar untuk mencakup seluruh history data
    }
    return mapping[range_option]

# def choose_sidebar_plot_range():
#     range_option = st.sidebar.radio("Pilih rentang visualisasi", ["1 Minggu Terakhir", "2 Minggu Terakhir", "1 Bulan Terakhir", "3 Bulan Terakhir", "6 Bulan Terakhir", "1 Tahun Terakhir"], horizontal=True)
#     mapping = {"1 Minggu Terakhir": 7, "2 Minggu Terakhir": 14, "1 Bulan Terakhir": 30, "3 Bulan Terakhir": 90, "6 Bulan Terakhir": 180, "1 Tahun Terakhir": 365}
#     return mapping[range_option]

def choose_sidebar_plot_range():
    options = [
        "1 Hari", "7 Hari", "1 Bulan", "3 Bulan", "5 Bulan", 
        "1 Tahun", "3 Tahun", "5 Tahun", "10 Tahun", "All Time"
    ]
    range_option = st.sidebar.radio("Pilih rentang visualisasi", options, horizontal=True)
    
    mapping = {
        "1 Hari": 1, 
        "7 Hari": 7, 
        "1 Bulan": 30, 
        "3 Bulan": 90, 
        "5 Bulan": 150, 
        "1 Tahun": 365,
        "3 Tahun": 1095,   # 365 * 3
        "5 Tahun": 1825,   # 365 * 5
        "10 Tahun": 3650,  # 365 * 10
        "All Time": 99999  # Angka besar untuk mencakup seluruh history data
    }
    return mapping[range_option]

def display_side_by_side_metrics(eval_metrics):
    """
    Menampilkan metrik komparasi (MAE, MAPE, RMSE, CI Coverage) 
    untuk ketiga model secara berdampingan.
    """
    if not eval_metrics:
        st.warning("Metrik evaluasi belum tersedia.")
        return
        
    st.markdown("### Perbandingan Performa Model")
    
    # Ubah dictionary hasil evaluasi menjadi DataFrame agar rapi
    df_metrics = pd.DataFrame(eval_metrics).T
    
    # Format angkanya supaya enak dibaca
    df_metrics['MAE'] = df_metrics['MAE'].apply(lambda x: f"Rp {x:,.2f}")
    df_metrics['RMSE'] = df_metrics['RMSE'].apply(lambda x: f"Rp {x:,.2f}")
    df_metrics['MAPE'] = df_metrics['MAPE'].apply(lambda x: f"{x:.2f}%")
    df_metrics['CI Coverage'] = df_metrics['CI Coverage'].apply(lambda x: f"{x:.0f}%")
    
    # Tampilkan tabel di Streamlit
    st.dataframe(df_metrics, use_container_width=True)