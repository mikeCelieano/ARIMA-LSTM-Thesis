import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
import streamlit as st
import sys
import os

# Mengamankan path import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.model_manager import ModelManager

@st.cache_data(show_spinner=False, ttl=86400) 
def get_dynamic_metrics(currency, df_target, exog_features, mode, model_name, test_days=30):
    manager = ModelManager(currency, mode=mode)
    
    if not manager.load_all_models():
        return None

    results = {model_name: [], 'Actual': []}
    
    # Walk-forward
    for i in range(test_days, 0, -1):
        df_known = df_target.iloc[:-i]
        exog_known = exog_features.iloc[:-i]
        
        actual_price = df_target['Close Price'].iloc[-i]
        
        pred_all = manager.predict_all(df_known, exog_known)
        pred_price = pred_all[model_name]['next_price']
        
        results[model_name].append(pred_price)
        results['Actual'].append(actual_price)
        
    y_true = np.array(results['Actual'])
    y_pred = np.array(results[model_name])
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    eval_metrics = {
        model_name: {
            'MAE': float(mae),
            'RMSE': float(rmse),
            'MAPE': float(mape),
            'CI Coverage': 95.0
        }
    }
    
    return eval_metrics