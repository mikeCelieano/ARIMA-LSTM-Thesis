from models.arima_model import ForexARIMA
from models.lstm_model import ForexLSTM
import pandas as pd

class ForexHybrid:
    def __init__(self, p=1, d=1, q=1, sequence_length=30):
        # Model ARIMA kita sekarang mengurus d=0 secara internal untuk Delta
        self.arima_base = ForexARIMA(p, d, q)
        self.lstm_residual = ForexLSTM(sequence_length)

    def _compute_residuals(self, df):
        # 1. Hitung Delta asli dari dataframe
        actual_delta = df['Close Price'].diff().dropna()

        # 2. Ambil prediksi in-sample ARIMA (Delta) dari fittedvalues
        # Ini lebih aman dan akurat daripada predict() karena index-nya dijamin presisi
        all_fitted = self.arima_base.model_fit.fittedvalues
        preds_delta = all_fitted.reindex(actual_delta.index).fillna(0)

        # 3. Residual = Error dari prediksi Delta
        residuals = actual_delta - preds_delta

        # 4. Smoothing untuk membuang noise tajam agar LSTM belajar tren error yang benar
        residuals = residuals.rolling(window=3).mean().fillna(0)

        return residuals

    def _make_residual_df(self, df, residuals):
        # TRIK PENTING UNTUK INTEGRASI LSTM:
        # Karena ForexLSTM otomatis melakukan .diff() pada kolom 'Close Price',
        # kita wajib memberikan "Cumulative Sum" dari residual.
        # Saat ForexLSTM melakukan .diff(), nilainya akan terurai kembali menjadi residual murni.
        df_res = df.copy().iloc[1:] # Buang baris 1 karena efek diff()
        df_res['Close Price'] = residuals.cumsum()
        return df_res

    def tune_and_train(self, df_train, exog_train):
        print("   -> [HYBRID] Step 1: ARIMA tuning...")
        self.arima_base.tune_and_train(df_train, exog_train)

        print("   -> [HYBRID] Step 2: Compute residuals...")
        residuals = self._compute_residuals(df_train)
        df_residual = self._make_residual_df(df_train, residuals)

        print("   -> [HYBRID] Step 3: LSTM tuning on residuals...")
        # Samakan index exog karena baris pertama df_residual baru saja di-drop
        exog_train_res = exog_train.reindex(df_residual.index).ffill().bfill()
        self.lstm_residual.tune_and_train(df_residual, exog_train_res)

    def train_initial(self, df_train, exog_train):
        self.arima_base.train_initial(df_train, exog_train)

        residuals = self._compute_residuals(df_train)
        df_residual = self._make_residual_df(df_train, residuals)

        exog_train_res = exog_train.reindex(df_residual.index).ffill().bfill()
        self.lstm_residual.train_initial(df_residual, exog_train_res)
        
    def incremental_train(self, latest_df, latest_exog):
        # 1. Update ARIMA base
        self.arima_base.append_data(latest_df, latest_exog)

        # 2. Generate history residual utuh dari dataframe terbaru yang masuk
        residuals_seq = self._compute_residuals(latest_df)
        df_res_seq = self._make_residual_df(latest_df, residuals_seq)
        exog_res_seq = latest_exog.reindex(df_res_seq.index).ffill().bfill()
        
        # 3. Update LSTM residual
        self.lstm_residual.incremental_train(df_res_seq, exog_res_seq)

    def forecast(self, df_recent, exog_recent):
        # 1. Base Prediction (Harga Absolut hasil rekonstruksi dari ARIMA)
        arima_res = self.arima_base.forecast(df_recent, exog_recent)
        base_pred = arima_res['next_price']

        # 2. Siapkan urutan data residual historis untuk LSTM
        residuals = self._compute_residuals(df_recent)
        df_res = self._make_residual_df(df_recent, residuals)
        exog_res = exog_recent.reindex(df_res.index).ffill().bfill()

        # 3. Prediksi Residual (Error Correction)
        lstm_res = self.lstm_residual.forecast(df_res, exog_res)
        
        # Ekstrak delta yang diprediksi LSTM (nilai ini adalah murni tebakan error/koreksi-nya)
        predicted_residual = lstm_res['delta_predicted']
        predicted_residual = predicted_residual * 0.8 # Dampen (redam) sedikit agar tidak over-react

        # 4. Final Prediction = Harga Prediksi Dasar + Tebakan Koreksi
        final_pred = base_pred + predicted_residual

        return {
            'next_price': float(final_pred),
            'lower_ci': float(arima_res['lower_ci'] + predicted_residual),
            'upper_ci': float(arima_res['upper_ci'] + predicted_residual)
        }