import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import keras_tuner as kt
import joblib

class ForexLSTM:
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()

    # 🔴 KONSEP BARU: Helper untuk menghitung Delta
    def _prepare_data_diff(self, df):
        df_diff = df.copy()
        df_diff['Price_Diff'] = df_diff['Close Price'].diff()
        return df_diff.dropna()

    def _prepare_sequences(self, X, y):
        X_seq, y_seq = [], []
        for i in range(len(X) - self.sequence_length):
            X_seq.append(X[i:(i + self.sequence_length)])
            y_seq.append(y[i + self.sequence_length])
        return np.array(X_seq), np.array(y_seq)

    def _build_tuner_model(self, hp):
        model = Sequential()

        units_1 = hp.Int('units_1', 32, 128, step=32)
        dropout_1 = hp.Float('dropout_1', 0.1, 0.4, step=0.1)

        model.add(LSTM(units_1, return_sequences=True,
                       input_shape=(self.sequence_length, self.n_features)))
        model.add(Dropout(dropout_1))

        units_2 = hp.Int('units_2', 32, 128, step=32)
        dropout_2 = hp.Float('dropout_2', 0.1, 0.4, step=0.1)

        model.add(LSTM(units_2, return_sequences=False))
        model.add(Dropout(dropout_2))

        dense_units = hp.Int('dense_units', 16, 64, step=16)
        model.add(Dense(dense_units))
        model.add(Dense(1))

        lr = hp.Choice('learning_rate', [1e-2, 1e-3, 1e-4])

        from tensorflow.keras.optimizers import Adam
        model.compile(optimizer=Adam(learning_rate=lr), loss='mse')

        return model

    def tune_and_train(self, df_train, exog_train,
                       max_trials=15, epochs=30, batch_size=32):

        print("   -> Tuning LSTM (Time-Series Aware - Delta Mode)...")

        # 🔴 Hitung Delta
        df_diff = self._prepare_data_diff(df_train)
        data = df_diff[['Close Price', 'Price_Diff']].join(exog_train).dropna()

        # 🔴 Target Y sekarang adalah 'Price_Diff', bukan 'Close Price'
        X_raw = data.drop(columns=['Close Price', 'Price_Diff']).values
        y_raw = data[['Price_Diff']].values

        self.n_features = X_raw.shape[1]

        split = int(len(X_raw) * 0.8)
        X_train_raw, X_val_raw = X_raw[:split], X_raw[split:]
        y_train_raw, y_val_raw = y_raw[:split], y_raw[split:]

        self.scaler_X.fit(X_train_raw)
        self.scaler_y.fit(y_train_raw)

        X_train = self.scaler_X.transform(X_train_raw)
        X_val = self.scaler_X.transform(X_val_raw)

        y_train = self.scaler_y.transform(y_train_raw)
        y_val = self.scaler_y.transform(y_val_raw)

        X_train_seq, y_train_seq = self._prepare_sequences(X_train, y_train)
        X_val_seq, y_val_seq = self._prepare_sequences(X_val, y_val)

        tuner = kt.BayesianOptimization(
            self._build_tuner_model,
            objective='val_loss',
            max_trials=max_trials,
            directory='tuning_logs',
            project_name='forex_lstm',
            overwrite=True
        )

        tuner.search(
            X_train_seq, y_train_seq,
            validation_data=(X_val_seq, y_val_seq),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )

        best_hps = tuner.get_best_hyperparameters(1)[0]

        print(f"   -> Best units1: {best_hps.get('units_1')}")
        print(f"   -> Best units2: {best_hps.get('units_2')}")
        print(f"   -> Best LR: {best_hps.get('learning_rate')}")

        self.model = tuner.hypermodel.build(best_hps)

        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )

        self.model.fit(
            X_train_seq, y_train_seq,
            validation_data=(X_val_seq, y_val_seq),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=1
        )

        print("   -> Final training selesai (no overfit).")

    def train_initial(self, df_train, exog_train,
                      epochs=50, batch_size=32):

        # 🔴 Hitung Delta
        df_diff = self._prepare_data_diff(df_train)
        data = df_diff[['Close Price', 'Price_Diff']].join(exog_train).dropna()

        X_raw = data.drop(columns=['Close Price', 'Price_Diff']).values
        y_raw = data[['Price_Diff']].values

        self.n_features = X_raw.shape[1]

        self.scaler_X.fit(X_raw)
        self.scaler_y.fit(y_raw)

        X = self.scaler_X.transform(X_raw)
        y = self.scaler_y.transform(y_raw)

        X_seq, y_seq = self._prepare_sequences(X, y)

        self.model = Sequential([
            LSTM(50, return_sequences=True,
                 input_shape=(self.sequence_length, self.n_features)),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])

        self.model.compile(optimizer='adam', loss='mse')

        self.model.fit(
            X_seq, y_seq,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )

    def incremental_train(self, latest_df, latest_exog, epochs=1):

        # 🔴 Hitung Delta untuk data harian terbaru
        df_diff = self._prepare_data_diff(latest_df)
        data = df_diff[['Close Price', 'Price_Diff']].join(latest_exog).dropna()

        X = self.scaler_X.transform(data.drop(columns=['Close Price', 'Price_Diff']).values)
        y = self.scaler_y.transform(data[['Price_Diff']].values)

        if len(X) < self.sequence_length:
            return

        X_seq = np.array([X[-self.sequence_length:]])
        y_seq = np.array([y[-1]])

        self.model.fit(X_seq, y_seq, epochs=epochs, verbose=1)

    def forecast(self, df_recent, exog_recent):

        # 🔴 1. Ambil harga terakhir sblm didiff untuk keperluan rekonstruksi di akhir
        last_actual_price = df_recent['Close Price'].iloc[-1]

        # 🔴 2. Siapkan data dengan Delta
        df_diff = self._prepare_data_diff(df_recent)
        data = df_diff[['Close Price', 'Price_Diff']].join(exog_recent).dropna()

        X = self.scaler_X.transform(data.drop(columns=['Close Price', 'Price_Diff']).values)

        if len(X) < self.sequence_length:
            raise ValueError("Data kurang untuk sequence.")

        X_seq = np.array([X[-self.sequence_length:]])

        # 🔴 3. Nilai pred_scaled ini sekarang melambangkan 'Selisih'
        pred_scaled = self.model.predict(X_seq, verbose=1)
        pred_delta = self.scaler_y.inverse_transform(pred_scaled)[0][0]

        # 🔴 4. REKONSTRUKSI: Harga Asli Terakhir + Prediksi Selisih
        final_price = last_actual_price + pred_delta

        return {
            'next_price': float(final_price),
            'delta_predicted': float(pred_delta),
            'lower_ci': float(final_price * 0.998), # Sedikit menyempitkan rasio CI krn model lbh akurat
            'upper_ci': float(final_price * 1.002)
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