import pandas as pd
import numpy as np
from utils.data_loader import combine_exog

def create_price_features(df):
    """
    Membuat fitur teknikal berdasarkan harga historis (Lag, Return, Spread).
    """
    df_feat = df.copy()
    
    # Fitur Lag (H-1)
    df_feat["Open_lag1"] = df_feat["Open"].shift(1)
    df_feat["High_lag1"] = df_feat["High"].shift(1)
    df_feat["Low_lag1"] = df_feat["Low"].shift(1)
    df_feat["Close_lag1"] = df_feat["Close Price"].shift(1)

    # Fitur Return & Spread
    df_feat["Return"] = df_feat["Close Price"].pct_change()
    df_feat["HL_Spread"] = df_feat["High"] - df_feat["Low"]

    return df_feat

def prepare_inference_data(df):
    """
    Menyiapkan data H-1 untuk diprediksi oleh UI Streamlit.
    Fungsi ini menggabungkan data forex dengan fitur dan data eksogen (BI & Inflasi).
    """
    # 1. Tarik data eksogen terbaru
    exog_data = combine_exog()
    
    # 2. Buat fitur harga
    df_features = create_price_features(df)
    
    # 3. Gabungkan data
    df_merged = df_features.join(exog_data, how="inner")
    
    # Tangani nilai tak terhingga (inf) dan kosong (NaN)
    df_merged = df_merged.replace([np.inf, -np.inf], np.nan)
    df_merged = df_merged.ffill().bfill().dropna()
    
    # 4. Pisahkan antara target dan fitur eksogen untuk dilempar ke model
    df_inference = df_merged[['Close Price']]
    exog_inference = df_merged[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]
    
    return df_inference, exog_inference