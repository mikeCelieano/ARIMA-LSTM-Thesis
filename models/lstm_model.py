import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
import keras_tuner as kt
import joblib
import os

class ForexLSTM:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()

    def _prepare_sequences(self, X, y):
        X_seq, y_seq = [], []
        for i in range(len(X) - self.sequence_length):
            X_seq.append(X[i:(i + self.sequence_length)])
            y_seq.append(y[i + self.sequence_length])
        return np.array(X_seq), np.array(y_seq)

    # Fungsi untuk KerasTuner membangun berbagai kombinasi arsitektur
    def _build_tuner_model(self, hp):
        model = Sequential()
        
        # Tuning jumlah neuron di layer LSTM pertama
        hp_units_1 = hp.Int('units_1', min_value=32, max_value=128, step=32)
        # Tuning tingkat Dropout untuk mencegah overfitting
        hp_dropout_1 = hp.Float('dropout_1', min_value=0.1, max_value=0.4, step=0.1)
        
        model.add(LSTM(hp_units_1, return_sequences=True, input_shape=(self.sequence_length, self.n_features)))
        model.add(Dropout(hp_dropout_1))
        
        hp_units_2 = hp.Int('units_2', min_value=32, max_value=128, step=32)
        hp_dropout_2 = hp.Float('dropout_2', min_value=0.1, max_value=0.4, step=0.1)
        
        model.add(LSTM(hp_units_2, return_sequences=False))
        model.add(Dropout(hp_dropout_2))
        
        hp_dense = hp.Int('dense_units', min_value=16, max_value=64, step=16)
        model.add(Dense(hp_dense))
        model.add(Dense(1))
        
        # Tuning learning rate
        hp_learning_rate = hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4])
        from tensorflow.keras.optimizers import Adam
        model.compile(optimizer=Adam(learning_rate=hp_learning_rate), loss='mse')
        
        return model

    def tune_and_train(self, df_train, exog_train, max_trials=5, epochs=30, batch_size=32):
        print("   -> Memulai KerasTuner Bayesian Optimization (Mencari arsitektur LSTM terbaik)...")
        data = df_train[['Close Price']].join(exog_train).dropna()
        X = data.drop(columns=['Close Price']).values
        y = data[['Close Price']].values

        self.n_features = X.shape[1] # Simpan untuk input_shape LSTM

        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y)
        X_seq, y_seq = self._prepare_sequences(X_scaled, y_scaled)

        # Inisialisasi Bayesian Tuner
        tuner = kt.BayesianOptimization(
            self._build_tuner_model,
            objective='val_loss',
            max_trials=max_trials,
            directory='tuning_logs',
            project_name='forex_lstm_tuning',
            overwrite=True # Timpa log lama jika di-run ulang
        )

        # Cari kombinasi terbaik (sisihkan 20% data untuk validasi skor)
        tuner.search(X_seq, y_seq, epochs=epochs, batch_size=batch_size, validation_split=0.2, verbose=1)

        # Ambil parameter terbaik
        best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]
        print(f"   -> [LSTM TUNED] Units L1: {best_hps.get('units_1')}, Dropout L1: {best_hps.get('dropout_1')}")
        print(f"   -> [LSTM TUNED] Units L2: {best_hps.get('units_2')}, Learning Rate: {best_hps.get('learning_rate')}")

        # Bangun ulang model dengan parameter jawara dan latih penuh ke seluruh data
        self.model = tuner.hypermodel.build(best_hps)
        self.model.fit(X_seq, y_seq, batch_size=batch_size, epochs=epochs, verbose=0)
        print("   -> Pelatihan akhir model LSTM Jawara selesai.")

    # --- FUNGSI DI BAWAH INI TETAP SAMA SEPERTI ASLINYA ---
    def train_initial(self, df_train, exog_train, epochs=50, batch_size=32):
        # Fallback jika hanya ingin run biasa tanpa tuning (kode asli kamu)
        # (Isi tetap sama persis seperti file asli yang kamu lampirkan)
        data = df_train[['Close Price']].join(exog_train).dropna()
        X = data.drop(columns=['Close Price']).values
        y = data[['Close Price']].values
        self.n_features = X.shape[1]
        
        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y)
        X_seq, y_seq = self._prepare_sequences(X_scaled, y_scaled)

        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(self.sequence_length, self.n_features)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse')
        self.model.fit(X_seq, y_seq, batch_size=batch_size, epochs=epochs, verbose=0)

    def incremental_train(self, latest_df, latest_exog, epochs=1):
        data = latest_df[['Close Price']].join(latest_exog).dropna()
        X = self.scaler_X.transform(data.drop(columns=['Close Price']).values)
        y = self.scaler_y.transform(data[['Close Price']].values)
        X_seq = np.array([X[-self.sequence_length:]])
        self.model.fit(X_seq, y, epochs=epochs, verbose=0)

    def forecast(self, df_recent, exog_recent):
        data = df_recent[['Close Price']].join(exog_recent).dropna()
        X = self.scaler_X.transform(data.drop(columns=['Close Price']).values)
        X_seq = np.array([X[-self.sequence_length:]])
        pred_scaled = self.model.predict(X_seq, verbose=0)
        pred_actual = self.scaler_y.inverse_transform(pred_scaled)[0][0]
        return {
            'next_price': pred_actual,
            'lower_ci': pred_actual * 0.995,
            'upper_ci': pred_actual * 1.005
        }
    
    def save(self, model_path, scaler_path_x, scaler_path_y):
        self.model.save(model_path)
        joblib.dump(self.scaler_X, scaler_path_x)
        joblib.dump(self.scaler_y, scaler_path_y)

    @classmethod
    def load(cls, model_path, scaler_path_x, scaler_path_y, sequence_length=30):
        instance = cls(sequence_length)
        instance.model = load_model(model_path)
        instance.scaler_X = joblib.load(scaler_path_x)
        instance.scaler_y = joblib.load(scaler_path_y)
        return instance