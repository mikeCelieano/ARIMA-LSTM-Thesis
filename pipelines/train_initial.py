import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.model_manager import ModelManager
from models.arima_model import ForexARIMA
from models.lstm_model import ForexLSTM
from models.hybrid_model import ForexHybrid

warnings.filterwarnings("ignore")

BULAN_MAP = {
    'januari': 'January', 'februari': 'February', 'maret': 'March',
    'april': 'April', 'mei': 'May', 'juni': 'June',
    'juli': 'July', 'agustus': 'August', 'september': 'September',
    'oktober': 'October', 'november': 'November', 'desember': 'December'
}

def clean_indo_date(series):
    s = series.astype(str).str.lower().str.strip()
    for indo, eng in BULAN_MAP.items():
        s = s.str.replace(indo, eng, regex=False)
    return s

def load_local_forex(currency):
    file_map = {
        "USD/IDR": "data/usd_idr.csv",
        "EUR/IDR": "data/eur_idr.csv",
        "GBP/IDR": "data/gbp_idr.csv"
    }
    
    df = pd.read_csv(file_map[currency])
    
    df.columns = [c.replace('"', '').strip() for c in df.columns]

    df = df.rename(columns={
        "Price": "Close Price"
    })

    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce').dt.tz_localize(None)
    df = df.dropna(subset=['Date']).set_index("Date").sort_index()

    df = df[~df.index.duplicated(keep='first')]

    for col in ["Open", "High", "Low", "Close Price"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(',', '', regex=False)
                .astype(float)
            )
            
    return df[["Open", "High", "Low", "Close Price"]]

def load_local_exog():
    # --- 1. BI RATE ---
    # Format: Tanggal, BI-7Day-RR (Contoh: 17 Maret 2026, 4.75%)
    bi = pd.read_csv("data/BI-7Day-RR.csv")
    bi.columns = [c.strip() for c in bi.columns]
    
    bi['Date'] = clean_indo_date(bi['Tanggal'])
    bi['Date'] = pd.to_datetime(bi['Date'], errors='coerce').dt.tz_localize(None)
    
    bi['BI Rate'] = (
        bi['BI-7Day-RR'].astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    
    bi = bi.dropna(subset=['Date']).set_index('Date').sort_index()
    bi = bi.reindex(pd.date_range(bi.index.min(), datetime.now(), freq='D')).ffill()

    # --- 2. INFLASI ---
    # Format: Periode, Data Inflasi (Contoh: Maret 2026, 3.48 %)
    inf = pd.read_csv("data/Data Inflasi.csv")
    inf.columns = [c.strip() for c in inf.columns]
    
    # Karena formatnya "Maret 2026", kita tambah awalan "1 " agar jadi tanggal
    inf['Date_Str'] = "1 " + clean_indo_date(inf['Periode'])
    inf['Date'] = pd.to_datetime(inf['Date_Str'], errors='coerce').dt.tz_localize(None)
    
    inf['Inflasi'] = (
        inf['Data Inflasi'].astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    
    inf = inf.dropna(subset=['Date']).set_index('Date').sort_index()
    inf = inf.reindex(pd.date_range(inf.index.min(), datetime.now(), freq="D")).ffill()

    # --- MERGE ---
    exog = inf[['Inflasi']].join(bi[['BI Rate']], how="outer").ffill().bfill()
    return exog

# =========================================================
# FEATURE ENGINEERING
# =========================================================
def create_local_features(df):
    df_feat = df.copy()
    # Shift 1 untuk menghindari look-ahead bias
    df_feat["Open_lag1"] = df_feat["Open"].shift(1)
    df_feat["High_lag1"] = df_feat["High"].shift(1)
    df_feat["Low_lag1"] = df_feat["Low"].shift(1)
    df_feat["Close_lag1"] = df_feat["Close Price"].shift(1)
    
    df_feat["Return"] = df_feat["Close Price"].pct_change()
    df_feat["HL_Spread"] = df_feat["High"] - df_feat["Low"]
    
    # Backfill agar baris pertama tidak hilang karena lag
    return df_feat.bfill()

# =========================================================
# MAIN TRAINING PIPELINE
# =========================================================
def run_initial_training(currency_list=["USD/IDR", "EUR/IDR", "GBP/IDR"]):
    print("🚀 Memulai Initial Training (Full History)...")

    exog_data = load_local_exog()
    print(f"✅ Data Eksogen dimuat: {len(exog_data)} baris.")

    for currency in currency_list:
        print(f"\n🔄 Memproses: {currency}")

        try:
            df_raw = load_local_forex(currency)
            print(f"📅 Forex Range: {df_raw.index.min().date()} s/d {df_raw.index.max().date()}")

            df_features = create_local_features(df_raw)
            df_merged = df_features.join(exog_data, how="left").bfill().ffill()
            
            # Buang baris yang benar-benar rusak total (biasanya tidak ada)
            df_merged = df_merged.dropna()

            print(f"✅ Data siap latih: {len(df_merged)} baris")

            df_train = df_merged[['Close Price']]
            exog_train = df_merged[
                ['Open_lag1','High_lag1','Low_lag1',
                 'Close_lag1','Return','HL_Spread',
                 'Inflasi','BI Rate']
            ]

            # ARIMA Params
            param_map = {"USD/IDR": (0,1,2), "EUR/IDR": (1,1,2), "GBP/IDR": (1,1,1)}
            p, d, q = param_map.get(currency, (1,1,1))

            for mode in ["baseline", "tuned"]:
                print(f"   🧠 MODE: {mode.upper()}")
                manager = ModelManager(currency, mode=mode)
                
                manager.arima = ForexARIMA(p=p, d=d, q=q)
                manager.lstm = ForexLSTM(sequence_length=30)
                manager.hybrid = ForexHybrid(p=p, d=d, q=q, sequence_length=30)

                if mode == "tuned":
                    manager.arima.tune_and_train(df_train, exog_train)  
                    manager.lstm.tune_and_train(df_train, exog_train, max_trials=10, epochs=30)
                    manager.hybrid.tune_and_train(df_train, exog_train)
                else:
                    manager.arima.train_initial(df_train, exog_train)
                    manager.lstm.train_initial(df_train, exog_train, epochs=30)
                    manager.hybrid.train_initial(df_train, exog_train)

                manager.save_all_models()
                print(f"   💾 Model {currency} ({mode}) tersimpan.")

        except Exception as e:
            print(f"❌ ERROR {currency}: {e}")
            continue

    print("\n🎉 Training Selesai!")

if __name__ == "__main__":
    run_initial_training()