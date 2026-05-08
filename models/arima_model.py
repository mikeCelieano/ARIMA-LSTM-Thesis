import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pmdarima as pm

class ForexARIMA:
    def __init__(self, p=1, d=1, q=1, use_exog=True):
        self.order = (p, d, q)
        self.model_fit = None
        self.use_exog = use_exog

    def _prepare_data(self, df, exog):
        """
        🔴 KONSEP BARU: Mengubah Harga Absolut menjadi Selisih Harga (Delta)
        """
        df_diff = df.copy()
        # Menghitung selisih harga dengan hari sebelumnya
        df_diff['Price_Diff'] = df_diff['Close Price'].diff()
        
        # Baris pertama pasti NaN karena tidak ada hari sebelumnya untuk dikurangi, jadi harus di-drop
        df_diff = df_diff.dropna() 
        
        y = df_diff['Price_Diff'].astype(float)

        # Samakan index variabel eksogen karena baris pertama 'y' baru saja di-drop
        if self.use_exog and exog is not None:
            exog = exog.reindex(y.index).ffill().bfill()
        else:
            exog = None

        return y, exog

    def tune_and_train(self, df_train, exog_train):
        print("   -> [ARIMA] Auto-tuning (robust mode) pada target Delta...")

        y, exog = self._prepare_data(df_train, exog_train)

        # 🔴 KUNCI: Karena data 'y' sudah berupa selisih (Delta), kita wajib menset d=0
        # agar auto_arima tidak melakukan differencing dua kali.
        auto_model = pm.auto_arima(
            y,
            X=exog,
            start_p=0, start_q=0,
            max_p=7, max_q=7,
            d=0,                    
            seasonal=False,
            trace=True,
            error_action='ignore',
            suppress_warnings=True,
            stepwise=True,
            information_criterion='aic',
            n_jobs=-1
        )

        # Simpan order terbaik (formatnya akan selalu p, 0, q)
        self.order = (auto_model.order[0], 0, auto_model.order[2])
        print(f"   -> [ARIMA TUNED] Best order for Delta: {self.order}")

        return self.train_initial(df_train, exog_train)

    def train_initial(self, df_train, exog_train):
        y, exog = self._prepare_data(df_train, exog_train)

        # Pastikan d=0 terpakai saat inisiasi SARIMAX
        order_to_use = (self.order[0], 0, self.order[2])

        model = SARIMAX(
            y,
            exog=exog,
            order=order_to_use,
            enforce_stationary=False,
            enforce_invertibility=False
        )

        self.model_fit = model.fit(disp=False)

        print(f"   -> [ARIMA TRAINED] AIC: {self.model_fit.aic:.2f}")

        return self.model_fit

    def append_data(self, df_recent, exog_recent):
        """
        Menambahkan data baru ke model secara incremental.
        Sekarang menerima dataframe utuh, mencari selisihnya, dan hanya mengambil hari terakhir.
        """
        # 1. Hitung seluruh Delta dari dataframe recent, lalu ambil HANYA 1 baris paling akhir
        y_all_delta, exog_all = self._prepare_data(df_recent, exog_recent)
        
        new_y_delta = y_all_delta.iloc[[-1]]
        new_X = exog_all.iloc[[-1]] if exog_all is not None else None

        # 2. CEK DUPLIKASI (Mencegah double-train di hari yang sama)
        try:
            last_date = self.model_fit.data.row_labels[-1]
            new_date = new_y_delta.index[0]
            if hasattr(last_date, 'date') and hasattr(new_date, 'date'):
                if new_date <= last_date:
                    print(f"   ⏭️ [ARIMA] Skip append! Data tanggal {new_date.date()} sudah ada di model (Last: {last_date.date()}).")
                    return
        except Exception:
            pass 

        # 3. COBA APPEND NORMAL
        try:
            # Yang dimasukkan ke model adalah nilai Delta-nya, bukan harga absolut
            self.model_fit = self.model_fit.append(endog=new_y_delta, exog=new_X, refit=False)
            
        except ValueError as e:
            # 4. FALLBACK: Copot index Pandas jadi murni Numpy Array
            print(f"   ⚠️ [ARIMA] Konflik index Pandas terdeteksi. Memaksa append via Numpy Array...")
            try:
                y_array = np.asarray(new_y_delta).flatten()
                X_array = np.asarray(new_X) if new_X is not None else None
                
                self.model_fit = self.model_fit.append(endog=y_array, exog=X_array, refit=False)
            except Exception as e2:
                print(f"   ❌ [ARIMA] Fallback tetap gagal: {e2}")
                raise e2

    def forecast(self, df_recent, exog_recent, steps=1):
        if self.model_fit is None:
            raise ValueError("Model belum dilatih.")

        # 🔴 Simpan harga H-1 untuk dipakai rekonstruksi di akhir
        last_actual_price = df_recent["Close Price"].iloc[-1]

        _, exog = self._prepare_data(df_recent, exog_recent)

        if exog is not None:
            last_exog = exog.iloc[[-1]].values
            future_exog = np.repeat(last_exog, steps, axis=0)
        else:
            future_exog = None

        forecast_obj = self.model_fit.get_forecast(
            steps=steps,
            exog=future_exog
        )

        # 🔴 Nilai yang keluar dari model ini adalah Prediksi Selisih Harga (Delta)
        pred_delta = forecast_obj.predicted_mean.iloc[-1]
        conf_delta = forecast_obj.conf_int().iloc[-1]

        # 🔴 REKONSTRUKSI: Harga Aktual Terakhir + Prediksi Selisih
        next_price = last_actual_price + pred_delta
        lower_ci = last_actual_price + conf_delta[0]
        upper_ci = last_actual_price + conf_delta[1]

        return {
            'next_price': float(next_price),          # Harga absolut untuk dikirim ke UI Streamlit
            'delta_predicted': float(pred_delta),     # Nilai delta murni (opsional, berguna untuk model Hybrid nantinya)
            'lower_ci': float(lower_ci),
            'upper_ci': float(upper_ci)
        }