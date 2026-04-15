import sys
import os
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Path fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.model_manager import ModelManager
from pipelines.train_initial import load_local_forex, load_local_exog, create_local_features


def run_backtest(currency, test_days=30):
    print(f"\n🔄 Running Backtest {test_days} Days for {currency}...")

    # =========================
    # 1. LOAD DATA
    # ======================== 
    exog_data = load_local_exog()
    df_raw = load_local_forex(currency)

    ten_years_ago = pd.Timestamp.now() - pd.DateOffset(years=10)
    df_raw = df_raw.loc[df_raw.index >= ten_years_ago]

    df_features = create_local_features(df_raw)
    df_merged = df_features.join(exog_data, how="inner").dropna()

    # =========================
    # 2. LOAD MODEL
    # =========================
    manager = ModelManager(currency)
    if not manager.load_all_models():
        print(f"❌ Model {currency} not found. Skipping.")
        return

    # =========================
    # 3. PREPARE STORAGE
    # =========================
    results = {
        'ARIMA': [],
        'LSTM': [],
        'ARIMA-LSTM Hybrid': [],
        'Actual': []
    }

    # =========================
    # 4. WALK-FORWARD BACKTEST
    # =========================
    for i in range(test_days, 0, -1):

        df_known = df_merged.iloc[:-i][['Close Price']]
        exog_known = df_merged[
            ['Open_lag1', 'High_lag1', 'Low_lag1',
             'Close_lag1', 'Return', 'HL_Spread',
             'Inflasi', 'BI Rate']
        ].iloc[:-i]

        actual_price = df_merged['Close Price'].iloc[-i]

        pred_all = manager.predict_all(df_known, exog_known)

        results['ARIMA'].append(pred_all['ARIMA']['next_price'])
        results['LSTM'].append(pred_all['LSTM']['next_price'])
        results['ARIMA-LSTM Hybrid'].append(pred_all['ARIMA-LSTM Hybrid']['next_price'])
        results['Actual'].append(actual_price)

    # =========================
    # 5. EVALUATION METRICS
    # =========================
    y_true = np.array(results['Actual'])

    print(f"\n✅ Backtest Completed!\n")
    print("eval_metrics = {")

    for model_name in ['ARIMA', 'LSTM', 'ARIMA-LSTM Hybrid']:
        y_pred = np.array(results[model_name])

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        # Directional Accuracy
        direction_true = np.sign(np.diff(y_true))
        direction_pred = np.sign(np.diff(y_pred))
        directional_acc = np.mean(direction_true == direction_pred) * 100

        print(f"    '{model_name}': {{")
        print(f"        'MAE': {mae:.4f},")
        print(f"        'RMSE': {rmse:.4f},")
        print(f"        'MAPE': {mape:.4f},")
        print(f"        'Directional Accuracy': {directional_acc:.2f}")
        print(f"    }},")

    print("}")
    print("=====================================================")


if __name__ == "__main__":
    currencies = ["USD/IDR", "EUR/IDR", "GBP/IDR"]
    for c in currencies:
        run_backtest(c, test_days=30)