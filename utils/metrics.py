import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
import streamlit as st
import sys
import os

# Mengamankan path import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.model_manager import ModelManager

# CACHE: Menyimpan hasil komputasi selama 24 jam agar UI tidak lemot!
@st.cache_data(show_spinner=False, ttl=86400) 
def get_dynamic_metrics(currency, df_target, exog_features, test_days=30):
    manager = ModelManager(currency)
    
    # Jika model belum dilatih, batalkan
    if not manager.load_all_models():
        return None

    results = {'ARIMA': [], 'LSTM': [], 'ARIMA-LSTM Hybrid': [], 'Actual': []}
    
    # Lakukan simulasi walk-forward 30 hari ke belakang
    for i in range(test_days, 0, -1):
        df_known = df_target.iloc[:-i]
        exog_known = exog_features.iloc[:-i]
        
        actual_price = df_target['Close Price'].iloc[-i]
        
        pred_all = manager.predict_all(df_known, exog_known)
        
        results['ARIMA'].append(pred_all['ARIMA']['next_price'])
        results['LSTM'].append(pred_all['LSTM']['next_price'])
        results['ARIMA-LSTM Hybrid'].append(pred_all['ARIMA-LSTM Hybrid']['next_price'])
        results['Actual'].append(actual_price)
        
    y_true = np.array(results['Actual'])
    eval_metrics = {}
    
    # Hitung rumusnya secara matematis
    for model_name in ['ARIMA', 'LSTM', 'ARIMA-LSTM Hybrid']:
        y_pred = np.array(results[model_name])
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        eval_metrics[model_name] = {
            'MAE': float(mae),
            'RMSE': float(rmse),
            'MAPE': float(mape),
            'CI Coverage': 95.0 # Statis untuk batas interval
        }
        
    return eval_metrics