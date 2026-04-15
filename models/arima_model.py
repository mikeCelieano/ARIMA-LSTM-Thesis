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
        y = df["Close Price"].astype(float)

        if self.use_exog and exog is not None:
            exog = exog.reindex(df.index).ffill().bfill()
        else:
            exog = None

        return y, exog

    def tune_and_train(self, df_train, exog_train):
        print("   -> [ARIMA] Auto-tuning (robust mode)...")

        y, exog = self._prepare_data(df_train, exog_train)

        # 🔴 Auto ARIMA (lebih luas & stabil)
        auto_model = pm.auto_arima(
            y,
            X=exog,
            start_p=0, start_q=0,
            max_p=7, max_q=7,
            d=None,                 # auto differencing
            seasonal=False,
            trace=True,
            error_action='ignore',
            suppress_warnings=True,
            stepwise=True,
            information_criterion='aic',
            n_jobs=-1
        )

        self.order = auto_model.order
        print(f"   -> [ARIMA TUNED] Best order: {self.order}")

        return self.train_initial(df_train, exog_train)

    def train_initial(self, df_train, exog_train):
        y, exog = self._prepare_data(df_train, exog_train)

        model = SARIMAX(
            y,
            exog=exog,
            order=self.order,
            enforce_stationary=False,
            enforce_invertibility=False
        )

        self.model_fit = model.fit(disp=False)

        print(f"   -> [ARIMA TRAINED] AIC: {self.model_fit.aic:.2f}")

        return self.model_fit

    def append_data(self, new_y, new_X):
        """
        Menambahkan data baru ke model ARIMA yang sudah dilatih.
        Dilengkapi dengan penanganan error index dan pencegahan duplikasi data.
        """
        # 1. CEK DUPLIKASI: Mencegah error jika data di hari yang sama di-train ulang
        try:
            last_date = self.model_fit.data.row_labels[-1]
            new_date = new_y.index[0]
            if hasattr(last_date, 'date') and hasattr(new_date, 'date'):
                if new_date <= last_date:
                    print(f"   ⏭️ [ARIMA] Skip append! Data tanggal {new_date.date()} sudah ada di model (Last: {last_date.date()}).")
                    return
        except Exception:
            pass # Lewati pengecekan jika index bukan datetime

        # 2. COBA APPEND NORMAL
        try:
            self.model_fit = self.model_fit.append(endog=new_y, exog=new_X, refit=False)
            
        except ValueError as e:
            # 3. FALLBACK: Copot index Pandas jadi murni Numpy Array
            print(f"   ⚠️ [ARIMA] Konflik index Pandas terdeteksi. Memaksa append via Numpy Array...")
            try:
                # np.asarray() membuang index Datetime dari pandas, sehingga statsmodels
                # akan mengabaikan validasi tanggal dan otomatis melanjutkannya ke n+1
                y_array = np.asarray(new_y).flatten()
                X_array = np.asarray(new_X)
                
                self.model_fit = self.model_fit.append(endog=y_array, exog=X_array, refit=False)
            except Exception as e2:
                print(f"   ❌ [ARIMA] Fallback tetap gagal: {e2}")
                raise e2

    def forecast(self, df_recent, exog_recent, steps=1):
        if self.model_fit is None:
            raise ValueError("Model belum dilatih.")

        _, exog = self._prepare_data(df_recent, exog_recent)

        # 🔴 handling future exog (lebih aman)
        if exog is not None:
            last_exog = exog.iloc[[-1]].values
            future_exog = np.repeat(last_exog, steps, axis=0)
        else:
            future_exog = None

        forecast_obj = self.model_fit.get_forecast(
            steps=steps,
            exog=future_exog
        )

        mean = forecast_obj.predicted_mean.iloc[-1]
        conf = forecast_obj.conf_int().iloc[-1]

        return {
            'next_price': float(mean),
            'lower_ci': float(conf[0]),
            'upper_ci': float(conf[1])
        }