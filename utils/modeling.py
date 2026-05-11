import pandas as pd
import numpy as np
from datetime import timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
from utils.data_loader import custom_bd

def backtest_model(df, exog, p, d, q, n_days=5):
    results = []

    df = df.dropna()
    exog = exog.reindex(df.index).ffill().bfill()

    exog = exog.dropna()
    df = df.loc[exog.index]

    for i in range(n_days, 0, -1):
        train_df = df.iloc[:-i]

        if len(train_df) < 30:
            continue

        train_exog = exog.loc[train_df.index]

        actual_date = df.index[-i]
        actual_price = df['Close Price'].iloc[-i]

        try:
            if actual_date not in exog.index:
                continue

            model = SARIMAX(
                train_df["Close Price"],
                exog=train_exog,
                order=(p, d, q),
                enforce_stationary=False,
                enforce_invertibility=False
            )

            model_fit = model.fit(disp=False)

            future_exog = exog.loc[[actual_date]]

            forecast_obj = model_fit.get_forecast(
                steps=1,
                exog=future_exog
            )

            predicted_price = forecast_obj.predicted_mean.iloc[0]
            conf_int = forecast_obj.conf_int().iloc[0]

            results.append({
                'Date': actual_date,
                'Actual': actual_price,
                'Predicted': predicted_price,
                'Lower_CI': conf_int[0],
                'Upper_CI': conf_int[1],
                'Within_CI': conf_int[0] <= actual_price <= conf_int[1],
                'Error': actual_price - predicted_price,
                'Error_Pct': ((actual_price - predicted_price) / actual_price) * 100
            })

        except Exception as e:
            import traceback
            print(f"\n❌ Error di tanggal {actual_date}")
            traceback.print_exc()
            continue

    result_df = pd.DataFrame(results)

    if result_df.empty:
        print("⚠️ Semua backtest gagal")

    return result_df

def arimax_1_horizon(df, exog, p, d, q, step, currency):
    import numpy as np
    import pandas as pd
    from datetime import timedelta
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from utils.data_loader import custom_bd

    df = df.copy().dropna()

    exog = exog.copy()
    exog = exog.reindex(df.index)

    exog = exog.replace([np.inf, -np.inf], np.nan)
    exog = exog.ffill().bfill()

    valid_idx = exog.dropna().index
    df = df.loc[valid_idx]
    exog = exog.loc[valid_idx]

    last_date = df.index[-1]

    model = SARIMAX(
        df["Close Price"],
        exog=exog,
        order=(p, d, q),
        enforce_stationary=False,
        enforce_invertibility=False
    )

    model_fit = model.fit(disp=False)

    # future_dates = pd.date_range(
    #     start=last_date + timedelta(days=1),
    #     periods=step,
    #     freq=custom_bd
    # )

    future_dates = pd.date_range(
        start=last_date + custom_bd,  # <-- Triknya di sini (langsung tambah custom_bd)
        periods=step,
        freq=custom_bd
    )

    last_exog = exog.iloc[-1]

    future_exog = pd.DataFrame(
        np.tile(last_exog.values, (step, 1)),
        index=future_dates,
        columns=exog.columns
    )

    forecast_obj = model_fit.get_forecast(
        steps=step,
        exog=future_exog
    )

    mean_forecast = forecast_obj.predicted_mean
    conf_int = forecast_obj.conf_int()

    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Forecast": mean_forecast.values,
        "Lower CI": conf_int.iloc[:, 0].values,
        "Upper CI": conf_int.iloc[:, 1].values
    })

    last_price = df['Close Price'].iloc[-1]
    next_price = mean_forecast.iloc[-1]

    perubahan_prediksi = next_price - last_price
    perubahan_persen = (perubahan_prediksi / last_price) * 100

    return {
        'forecast_df': forecast_df,
        'last_date': last_date,
        'last_price': last_price,
        'next_price': next_price,
        'future_dates': future_dates,
        'perubahan_prediksi': perubahan_prediksi,
        'perubahan_persen': perubahan_persen,
        'upper_ci': forecast_df["Upper CI"].iloc[0],
        'lower_ci': forecast_df["Lower CI"].iloc[0],
        'expected_return': perubahan_persen,
        'currency': currency
    }
