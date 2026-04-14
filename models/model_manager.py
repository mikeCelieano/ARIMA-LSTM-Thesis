import os
import joblib
import numpy as np
import pandas as pd
# Asumsi kita akan mengimpor definisi kelas dari file lain
from models.arima_model import ForexARIMA
from models.lstm_model import ForexLSTM
from models.hybrid_model import ForexHybrid

class ModelManager:
    """
    Manajer terpusat untuk load model, prediksi, dan menyimpan model.
    Dioptimalkan agar Streamlit bisa memanggil model dengan cepat.
    """

    def __init__(self, currency, mode="tuned", base_path="saved_models/"):
        self.currency = currency.replace("/", "_")
        self.mode = mode.lower()  # "tuned" / "baseline"
        
        self.model_dir = os.path.join(base_path, self.currency, self.mode)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.arima = None
        self.lstm = None
        self.hybrid = None

    def load_all_models(self):
        try:
            print(f"📂 Loading models from: {self.model_dir}")

            self.arima = joblib.load(os.path.join(self.model_dir, "arima.pkl"))

            self.lstm = ForexLSTM.load(
                os.path.join(self.model_dir, "lstm.keras"),
                os.path.join(self.model_dir, "scaler_x.pkl"),
                os.path.join(self.model_dir, "scaler_y.pkl")
            )

            self.hybrid = joblib.load(os.path.join(self.model_dir, "hybrid.pkl"))

            return True
        except FileNotFoundError:
            print(f"❌ Model tidak ditemukan di {self.model_dir}")
            return False

    def predict_all(self, df_recent, exog_recent):
        """Menghasilkan prediksi dari ketiga model untuk komparasi UI"""
        if not self.arima or not self.lstm or not self.hybrid:
            self.load_all_models()

        res_arima = self.arima.forecast(df_recent, exog_recent)
        res_lstm = self.lstm.forecast(df_recent, exog_recent)
        res_hybrid = self.hybrid.forecast(df_recent, exog_recent)

        return {
            "ARIMA": res_arima,
            "LSTM": res_lstm,
            "ARIMA-LSTM Hybrid": res_hybrid
        }

    def evaluate_models(self, actual, predictions):
        """Mengirim data ke utils/evaluation.py untuk menghitung metrik"""
        from utils.evaluation import calculate_comprehensive_metrics
        return calculate_comprehensive_metrics(actual, predictions)
    
    def save_all_models(self):
        """Menyimpan ketiga model ke dalam hard drive"""
        if not self.arima or not self.lstm or not self.hybrid:
            raise ValueError("Model belum di-train, tidak ada yang bisa disimpan.")
            
        joblib.dump(self.arima, os.path.join(self.model_dir, "arima.pkl"))
        
        self.lstm.save(
            os.path.join(self.model_dir, "lstm.keras"),
            os.path.join(self.model_dir, "scaler_x.pkl"),
            os.path.join(self.model_dir, "scaler_y.pkl")
        )
        
        joblib.dump(self.hybrid, os.path.join(self.model_dir, "hybrid.pkl"))