from models.arima_model import ForexARIMA
from models.lstm_model import ForexLSTM
import pandas as pd

class ForexHybrid:
    def __init__(self, p=1, d=1, q=1, sequence_length=30):
        self.arima_base = ForexARIMA(p, d, q)
        self.lstm_residual = ForexLSTM(sequence_length)

    def tune_and_train(self, df_train, exog_train):
        print("   -> [HYBRID] Langkah 1: Tuning & Latih ARIMA Base...")
        # Tuning ARIMA
        model_fit = self.arima_base.tune_and_train(df_train, exog_train)
        
        # Ekstrak residual
        predictions_arima = model_fit.fittedvalues
        residuals = df_train['Close Price'] - predictions_arima
        
        df_residual = df_train.copy()
        df_residual['Close Price'] = residuals 
        
        print("   -> [HYBRID] Langkah 2: Tuning & Latih LSTM terhadap Residual...")
        # Tuning LSTM khusus untuk residual
        self.lstm_residual.tune_and_train(df_residual, exog_train)

    def train_initial(self, df_train, exog_train):
        # (Fungsi asli kamu biarkan utuh sebagai fallback)
        model_fit = self.arima_base.train_initial(df_train, exog_train)
        
        predictions_arima = model_fit.fittedvalues
        residuals = df_train['Close Price'] - predictions_arima
        
        df_residual = df_train.copy()
        df_residual['Close Price'] = residuals 
        
        self.lstm_residual.train_initial(df_residual, exog_train)

    def incremental_train(self, latest_df, latest_exog):
        self.arima_base.append_data(latest_df, latest_exog)
        
        pred_arima = self.arima_base.forecast(latest_df, latest_exog)['next_price']
        residual = latest_df['Close Price'].iloc[-1] - pred_arima
        
        latest_res_df = latest_df.copy()
        latest_res_df['Close Price'] = residual
        
        self.lstm_residual.incremental_train(latest_res_df, latest_exog)

    def forecast(self, df_recent, exog_recent):
        arima_res = self.arima_base.forecast(df_recent, exog_recent)
        base_pred = arima_res['next_price']
        
        residual_pred = self.lstm_residual.forecast(df_recent, exog_recent)['next_price']
        
        final_pred = base_pred + residual_pred
        
        return {
            'next_price': final_pred,
            'lower_ci': arima_res['lower_ci'] + residual_pred,
            'upper_ci': arima_res['upper_ci'] + residual_pred
        }