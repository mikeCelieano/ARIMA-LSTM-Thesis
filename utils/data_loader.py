import pandas as pd
from datetime import timedelta
import holidays
from pandas.tseries.offsets import CustomBusinessDay
import streamlit as st
import numpy as np
import requests
import os
import logging # Tambahan untuk logging error ke terminal
from dotenv import load_dotenv

years = range(2025, 2027)
id_holidays = holidays.Indonesia(years=years)
holiday_dates = pd.to_datetime(list(id_holidays.keys()))
custom_bd = CustomBusinessDay(holidays=holiday_dates)

@st.cache_data(ttl=3600)
def load_local_fallback(currency_symbol):
    """Fungsi pembantu membaca data CSV lokal secara diam-diam jika API gagal."""
    file_map = {"USD": "data/usd_idr.csv", "EUR": "data/eur_idr.csv", "GBP": "data/gbp_idr.csv"}
    try:
        df = pd.read_csv(file_map[currency_symbol])
        
        col_date = df.columns[0]
        col_close = df.columns[1]
        col_open = df.columns[2]
        col_high = df.columns[3]
        col_low = df.columns[4]
        
        df = df.rename(columns={col_date: "Date", col_close: "Close Price", col_open: "Open", col_high: "High", col_low: "Low"})
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce', format='mixed').dt.tz_localize(None)
        df = df.dropna(subset=['Date'])
        df = df.set_index("Date").sort_index()
        
        for col in ["Open", "High", "Low", "Close Price"]:
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False).astype(float)
        return df[["Open", "High", "Low", "Close Price"]]
    except Exception as e:
        logging.error(f"Gagal memuat file lokal untuk {currency_symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_forex_investing(base_curr):
    """
    Fungsi pengganti Alpha Vantage.
    Sekarang sudah termasuk kolom Change % untuk keperluan visualisasi.
    """
    file_map = {
        "USD": "data/usd_idr.csv", 
        "EUR": "data/eur_idr.csv", 
        "GBP": "data/gbp_idr.csv"
    }
    file_path = file_map.get(base_curr)
    
    if not file_path or not os.path.exists(file_path):
        logging.error(f"File {file_path} tidak ditemukan.")
        return load_local_fallback(base_curr)

    try:
        df = pd.read_csv(file_path)

        # 1. Konversi Tanggal
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce').dt.tz_localize(None)
        df = df.dropna(subset=['Date']).set_index("Date").sort_index()

        # 2. Membersihkan angka (Open, High, Low, Price)
        target_cols = ["Price", "Open", "High", "Low"]
        for col in target_cols:
            if col in df.columns:
                df[col] = (
                    df[col].astype(str)
                    .str.replace(',', '', regex=False)
                    .astype(float)
                )

        # 3. Membersihkan Change % (Contoh: "+0.15%" -> 0.15)
        if "Change %" in df.columns:
            df["Change %"] = (
                df["Change %"].astype(str)
                .str.replace('%', '', regex=False)
                .str.replace('+', '', regex=False)
                .astype(float)
            )

        # 4. Standarisasi Nama Kolom
        df = df.rename(columns={"Price": "Close Price"})

        # Sekarang kita return 5 kolom!
        return df[["Open", "High", "Low", "Close Price", "Change %"]]
        
    except Exception as e:
        logging.error(f"Gagal memproses file {file_path}: {e}")
        return load_local_fallback(base_curr)

@st.cache_data(ttl=3600)
def load_usd(): 
    return fetch_forex_investing("USD")

@st.cache_data(ttl=3600)
def load_eur(): 
    return fetch_forex_investing("EUR")

@st.cache_data(ttl=3600)
def load_gbp(): 
    return fetch_forex_investing("GBP")

def exog_birate():
    bulan_mapping = {'januari': 'January', 'februari': 'February', 'maret': 'March', 'april': 'April', 'mei': 'May', 'juni': 'June', 'juli': 'July', 'agustus': 'August', 'september': 'September', 'oktober': 'October', 'november': 'November', 'desember': 'December'}
    temp_bi = pd.read_csv("data/BI-7Day-RR.csv", header=None)
    header_idx_bi = 0
    for i, row in temp_bi.iterrows():
        if any(isinstance(v, str) and ('tanggal' in v.lower() or 'date' in v.lower() or 'periode' in v.lower()) for v in row):
            header_idx_bi = i
            break
            
    int_rate = pd.read_csv("data/BI-7Day-RR.csv", header=header_idx_bi)
    date_col = [c for c in int_rate.columns if 'tanggal' in str(c).lower() or 'date' in str(c).lower() or 'periode' in str(c).lower()][0]
    rate_col = [c for c in int_rate.columns if 'bi' in str(c).lower() or 'rate' in str(c).lower() or '7day' in str(c).lower()][0]
    
    int_rate = int_rate[[date_col, rate_col]].copy()
    int_rate.rename(columns={date_col: "Date", rate_col: "BI Rate"}, inplace=True)
    int_rate['Date'] = int_rate['Date'].astype(str).str.lower()
    for indo, eng in bulan_mapping.items(): int_rate['Date'] = int_rate['Date'].str.replace(indo, eng, regex=False)
    int_rate['Date'] = pd.to_datetime(int_rate['Date'], errors='coerce').dt.tz_localize(None)
    int_rate['BI Rate'] = int_rate['BI Rate'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    int_rate = int_rate.dropna(subset=['Date', 'BI Rate']).set_index('Date').sort_index()
    if not int_rate.empty:
        int_rate = int_rate.reindex(pd.date_range(int_rate.index.min(), int_rate.index.max(), freq='D')).ffill()
    return int_rate

def exog_inflasi():
    bulan_mapping = {'januari': 'January', 'februari': 'February', 'maret': 'March', 'april': 'April', 'mei': 'May', 'juni': 'June', 'juli': 'July', 'agustus': 'August', 'september': 'September', 'oktober': 'October', 'november': 'November', 'desember': 'December'}
    temp_inf = pd.read_csv("data/Data Inflasi.csv", header=None)
    start_row = 0; date_col_idx = 0
    for i, row in temp_inf.iterrows():
        row_str = " ".join([str(x).lower() for x in row.values])
        if any(b in row_str for b in bulan_mapping.keys()):
            start_row = i
            for j, val in enumerate(row.values):
                if isinstance(val, str) and any(b in val.lower() for b in bulan_mapping.keys()):
                    date_col_idx = j; break
            break
            
    inflasi = temp_inf.iloc[start_row:].copy()
    inflasi = inflasi[[inflasi.columns[date_col_idx], inflasi.columns[date_col_idx + 1]]]
    inflasi.columns = ['Date', 'Inflasi']
    inflasi['Date'] = inflasi['Date'].astype(str).str.lower()
    for indo, eng in bulan_mapping.items(): inflasi['Date'] = inflasi['Date'].str.replace(indo, eng, regex=False)
    inflasi['Inflasi'] = inflasi['Inflasi'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    inflasi['Date'] = pd.to_datetime(inflasi['Date'], errors='coerce', format='mixed').dt.tz_localize(None)
    inflasi = inflasi.dropna(subset=['Date', 'Inflasi']).set_index('Date').sort_index()
    if not inflasi.empty:
        inflasi = inflasi.reindex(pd.date_range(inflasi.index.min(), inflasi.index.max(), freq="D")).ffill()
    return inflasi

def combine_exog():
    exog = exog_inflasi().join(exog_birate(), how="outer").replace([np.inf, -np.inf], np.nan).ffill().bfill().dropna()
    return exog

df_map = {'USD/IDR': load_usd, 'EUR/IDR': load_eur, 'GBP/IDR': load_gbp}