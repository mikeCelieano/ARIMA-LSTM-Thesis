import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Mengarahkan path agar bisa membaca modul dari folder root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.model_manager import ModelManager
from models.arima_model import ForexARIMA
from models.lstm_model import ForexLSTM
from models.hybrid_model import ForexHybrid

import warnings 
warnings.filterwarnings("ignore")

def load_local_forex(currency):
    file_map = {
        "USD/IDR": "data/usd_idr.csv",
        "EUR/IDR": "data/eur_idr.csv",
        "GBP/IDR": "data/gbp_idr.csv"
    }
    df = pd.read_csv(file_map[currency])
    
    col_date = df.columns[0]
    col_close = df.columns[1]
    col_open = df.columns[2]
    col_high = df.columns[3]
    col_low = df.columns[4]
    
    df = df.rename(columns={
        col_date: "Date",
        col_close: "Close Price",
        col_open: "Open",
        col_high: "High",
        col_low: "Low"
    })
    
    # Konversi tanggal dan lucuti zona waktu agar join tidak meleset
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce', format='mixed').dt.tz_localize(None)
    df = df.dropna(subset=['Date'])
    df = df.set_index("Date").sort_index()
    
    for col in ["Open", "High", "Low", "Close Price"]:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).astype(float)
            
    return df[["Open", "High", "Low", "Close Price"]]

def load_local_exog():
    # Pastikan dictionary huruf kecil semua untuk pencarian kebal-kapital
    bulan_mapping = {
        'januari': 'January', 'februari': 'February', 'maret': 'March',
        'april': 'April', 'mei': 'May', 'juni': 'June',
        'juli': 'July', 'agustus': 'August', 'september': 'September',
        'oktober': 'October', 'november': 'November', 'desember': 'December'
    }

    # --- 1. BI RATE ---
    temp_bi = pd.read_csv("data/BI-7Day-RR.csv", header=None)
    header_idx_bi = 0
    for i, row in temp_bi.iterrows():
        if any(isinstance(v, str) and ('tanggal' in v.lower() or 'date' in v.lower() or 'periode' in v.lower()) for v in row):
            header_idx_bi = i
            break
            
    int_rate = pd.read_csv("data/BI-7Day-RR.csv", header=header_idx_bi)
    date_col_bi = [c for c in int_rate.columns if 'tanggal' in str(c).lower() or 'date' in str(c).lower() or 'periode' in str(c).lower()][0]
    rate_col_bi = [c for c in int_rate.columns if 'bi' in str(c).lower() or 'rate' in str(c).lower() or '7day' in str(c).lower()][0]
    
    int_rate = int_rate[[date_col_bi, rate_col_bi]].copy()
    int_rate.rename(columns={date_col_bi: "Date", rate_col_bi: "BI Rate"}, inplace=True)
    
    # Paksa menjadi huruf kecil sebelum di-replace
    int_rate['Date'] = int_rate['Date'].astype(str).str.lower()
    for indo, eng in bulan_mapping.items():
        int_rate['Date'] = int_rate['Date'].str.replace(indo, eng, regex=False)
        
    int_rate['Date'] = pd.to_datetime(int_rate['Date'], errors='coerce').dt.tz_localize(None)
    int_rate['BI Rate'] = int_rate['BI Rate'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    int_rate = int_rate.dropna(subset=['Date', 'BI Rate']).set_index('Date').sort_index()
    if not int_rate.empty:
        int_rate = int_rate.reindex(pd.date_range(int_rate.index.min(), int_rate.index.max(), freq='D')).ffill()

    # --- 2. INFLASI ---
    temp_inf = pd.read_csv("data/Data Inflasi.csv", header=None)
    start_row = 0
    date_col_idx = 0
    
    for i, row in temp_inf.iterrows():
        row_str = " ".join([str(x).lower() for x in row.values])
        if any(b in row_str for b in bulan_mapping.keys()):
            start_row = i
            for j, val in enumerate(row.values):
                if isinstance(val, str) and any(b in val.lower() for b in bulan_mapping.keys()):
                    date_col_idx = j
                    break
            break
            
    inf_col_idx = date_col_idx + 1 
    
    inflasi = temp_inf.iloc[start_row:].copy()
    inflasi = inflasi[[inflasi.columns[date_col_idx], inflasi.columns[inf_col_idx]]]
    inflasi.columns = ['Date', 'Inflasi']
    
    # Paksa menjadi huruf kecil sebelum di-replace
    inflasi['Date'] = inflasi['Date'].astype(str).str.lower()
    for indo, eng in bulan_mapping.items():
        inflasi['Date'] = inflasi['Date'].str.replace(indo, eng, regex=False)
        
    inflasi['Inflasi'] = inflasi['Inflasi'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    inflasi['Date'] = pd.to_datetime(inflasi['Date'], errors='coerce', format='mixed').dt.tz_localize(None)
    inflasi = inflasi.dropna(subset=['Date', 'Inflasi']).set_index('Date').sort_index()
    if not inflasi.empty:
        inflasi = inflasi.reindex(pd.date_range(inflasi.index.min(), inflasi.index.max(), freq="D")).ffill()

    # --- GABUNGKAN EKSOGEN DENGAN OUTER JOIN ---
    exog = inflasi.join(int_rate, how="outer").replace([np.inf, -np.inf], np.nan).ffill().bfill().dropna()
    return exog

def create_local_features(df):
    df_feat = df.copy()
    df_feat["Open_lag1"] = df_feat["Open"].shift(1)
    df_feat["High_lag1"] = df_feat["High"].shift(1)
    df_feat["Low_lag1"] = df_feat["Low"].shift(1)
    df_feat["Close_lag1"] = df_feat["Close Price"].shift(1)
    df_feat["Return"] = df_feat["Close Price"].pct_change()
    df_feat["HL_Spread"] = df_feat["High"] - df_feat["Low"]
    return df_feat

def run_initial_training(
    currency_list=["USD/IDR", "EUR/IDR", "GBP/IDR"]
):
    print("🚀 Memulai Initial Training (Baseline + Tuned)...")

    # =========================
    # LOAD EXOGEN
    # =========================
    print("\n📥 Menarik data eksogen (Inflasi & BI Rate)...")
    exog_data = load_local_exog()
    print(f"✅ Data Eksogen berhasil dimuat: {len(exog_data)} baris.")

    # =========================
    # LOOP PER CURRENCY
    # =========================
    for currency in currency_list:
        print("\n=========================================")
        print(f"🔄 Memproses model: {currency}")
        print("=========================================")

        try:
            # =========================
            # LOAD DATA
            # =========================
            df_raw = load_local_forex(currency)

            ten_years_ago = datetime.now() - pd.DateOffset(years=10)
            df_raw = df_raw.loc[df_raw.index >= ten_years_ago]

            print(f"✅ Data Forex: {df_raw.index.min().strftime('%Y-%m-%d')} → {df_raw.index.max().strftime('%Y-%m-%d')}")

            # =========================
            # FEATURE
            # =========================
            df_features = create_local_features(df_raw)
            df_merged = df_features.join(exog_data, how="inner").dropna()

            print(f"✅ Data siap latih: {len(df_merged)} baris")

            if df_merged.empty:
                print(f"❌ Data kosong. Skip.")
                continue

            df_train = df_merged[['Close Price']]
            exog_train = df_merged[
                ['Open_lag1','High_lag1','Low_lag1',
                 'Close_lag1','Return','HL_Spread',
                 'Inflasi','BI Rate']
            ]

            param_map = {
                "USD/IDR": (0, 1, 2),
                "EUR/IDR": (1, 1, 2),
                "GBP/IDR": (1, 1, 1)
            }
            p, d, q = param_map.get(currency, (1,1,1))

            # ==========================================
            # 🔥 LOOP MODE DI SINI (KUNCI UTAMA)
            # ==========================================
            for mode in ["baseline", "tuned"]:
                print(f"\n🧠 MODE: {mode.upper()}")

                manager = ModelManager(currency, mode=mode)

                manager.arima = ForexARIMA(p=p, d=d, q=q)
                manager.lstm = ForexLSTM(sequence_length=30)
                manager.hybrid = ForexHybrid(p=p, d=d, q=q, sequence_length=30)

                if mode == "tuned":
                    print("   -> Training TUNED models...")
                    manager.arima.tune_and_train(df_train, exog_train)
                    manager.lstm.tune_and_train(df_train, exog_train, max_trials=10, epochs=30)
                    manager.hybrid.tune_and_train(df_train, exog_train)

                else:
                    print("   -> Training BASELINE models...")
                    manager.arima.train_initial(df_train, exog_train)
                    manager.lstm.train_initial(df_train, exog_train, epochs=30)
                    manager.hybrid.train_initial(df_train, exog_train)

                print(f"💾 Save ke saved_models/{currency.replace('/', '_')}/{mode}")
                manager.save_all_models()

                print(f"✅ Done {currency} ({mode})")

        except Exception as e:
            print(f"❌ ERROR {currency}: {e}")
            continue

    print("\n🎉 Semua model (baseline + tuned) berhasil dibuat!")

if __name__ == "__main__":
    run_initial_training()