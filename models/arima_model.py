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

    def append_data(self, new_df, new_exog):
        if self.model_fit is None:
            raise ValueError("Model belum diinisialisasi.")

        y_new, exog_new = self._prepare_data(new_df, new_exog)

        # 🔴 penting: jangan refit tiap step
        self.model_fit = self.model_fit.append(
            endog=y_new,
            exog=exog_new,
            refit=False
        )

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