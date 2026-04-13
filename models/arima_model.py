import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pmdarima as pm

class ForexARIMA:
    def __init__(self, p=1, d=1, q=1):
        self.order = (p, d, q)
        self.model_fit = None

    def tune_and_train(self, df_train, exog_train):
        print("   -> Memulai pencarian Auto-ARIMA (Smarter GridSearch)...")
        # auto_arima akan mencari kombinasi p, d, q terbaik secara otomatis
        auto_model = pm.auto_arima(
            df_train["Close Price"],
            X=exog_train,
            start_p=0, start_q=0,
            max_p=5, max_q=5,
            seasonal=False, # Karena ini data harian valas
            trace=True,     # Menampilkan log proses di terminal
            error_action='ignore',
            suppress_warnings=True,
            stepwise=True   # Algoritma pencarian cerdas (lebih cepat dari full GridSearch)
        )
        
        # Simpan order terbaik yang ditemukan
        self.order = auto_model.order
        print(f"   -> [ARIMA TUNED] Parameter terbaik ditemukan: {self.order}")
        
        # Latih model menggunakan statsmodels bawaan agar kompatibel dengan update harian
        return self.train_initial(df_train, exog_train)

    def train_initial(self, df_train, exog_train):
        model = SARIMAX(
            df_train["Close Price"],
            exog=exog_train,
            order=self.order,
            enforce_stationary=False,
            enforce_invertibility=False
        )
        self.model_fit = model.fit(disp=False)
        return self.model_fit

    def append_data(self, new_df, new_exog):
        if self.model_fit is None:
            raise ValueError("Model belum diinisialisasi. Lakukan train_initial terlebih dahulu.")
            
        y_new = new_df["Close Price"].values
        X_new = new_exog.values
        self.model_fit = self.model_fit.append(endog=y_new, exog=X_new, refit=True)

    def forecast(self, df_recent, exog_recent, steps=1):
        future_exog = exog_recent.iloc[[-1]].copy()
        if steps > 1:
            future_exog = pd.concat([future_exog]*steps, ignore_index=True)
            
        forecast_obj = self.model_fit.get_forecast(steps=steps, exog=future_exog)
        return {
            'next_price': forecast_obj.predicted_mean.iloc[-1],
            'lower_ci': forecast_obj.conf_int().iloc[-1, 0],
            'upper_ci': forecast_obj.conf_int().iloc[-1, 1]
        }