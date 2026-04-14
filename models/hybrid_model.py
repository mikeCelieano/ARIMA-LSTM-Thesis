from models.arima_model import ForexARIMA
from models.lstm_model import ForexLSTM
import pandas as pd

class ForexHybrid:
    def __init__(self, p=1, d=1, q=1, sequence_length=30):
        self.arima_base = ForexARIMA(p, d, q)
        self.lstm_residual = ForexLSTM(sequence_length)

    def _compute_residuals(self, df, model_fit):
        # 🔴 Prediksi aligned (lebih akurat dari fittedvalues)
        preds = model_fit.predict(start=0, end=len(df)-1)

        residuals = df['Close Price'] - preds

        # 🔴 Smoothing biar LSTM nggak belajar noise
        residuals = residuals.rolling(window=3).mean().fillna(0)

        return residuals

    def tune_and_train(self, df_train, exog_train):
        print("   -> [HYBRID] Step 1: ARIMA tuning...")
        model_fit = self.arima_base.tune_and_train(df_train, exog_train)

        print("   -> [HYBRID] Step 2: Compute residuals...")
        residuals = self._compute_residuals(df_train, model_fit)

        df_residual = df_train.copy()
        df_residual['Close Price'] = residuals

        print("   -> [HYBRID] Step 3: LSTM tuning on residuals...")
        self.lstm_residual.tune_and_train(df_residual, exog_train)

    def train_initial(self, df_train, exog_train):
        model_fit = self.arima_base.train_initial(df_train, exog_train)

        residuals = self._compute_residuals(df_train, model_fit)

        df_residual = df_train.copy()
        df_residual['Close Price'] = residuals

        self.lstm_residual.train_initial(df_residual, exog_train)

    def incremental_train(self, latest_df, latest_exog):
        # Update ARIMA
        self.arima_base.append_data(latest_df, latest_exog)

        # Hitung residual terbaru
        pred_arima = self.arima_base.forecast(latest_df, latest_exog)['next_price']
        actual = latest_df['Close Price'].iloc[-1]

        residual = actual - pred_arima

        # Optional smoothing kecil
        residual = residual * 0.7  # dampen noise

        latest_res_df = latest_df.copy()
        latest_res_df['Close Price'] = residual

        self.lstm_residual.incremental_train(latest_res_df, latest_exog)

    def forecast(self, df_recent, exog_recent):
        arima_res = self.arima_base.forecast(df_recent, exog_recent)
        base_pred = arima_res['next_price']

        residual_pred = self.lstm_residual.forecast(df_recent, exog_recent)['next_price']

        # 🔴 Optional: batasi kontribusi residual (biar nggak over-adjust)
        residual_pred = residual_pred * 0.8

        final_pred = base_pred + residual_pred

        return {
            'next_price': final_pred,
            'lower_ci': arima_res['lower_ci'] + residual_pred,
            'upper_ci': arima_res['upper_ci'] + residual_pred
        }