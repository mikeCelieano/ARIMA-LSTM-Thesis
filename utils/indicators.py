import pandas as pd

def calculate_macd(df, fast=12, slow=26, signal=9):
    df_macd = df.copy()
    ema_fast = df_macd['Close Price'].ewm(span=fast, adjust=False).mean()
    ema_slow = df_macd['Close Price'].ewm(span=slow, adjust=False).mean()
    df_macd['MACD'] = ema_fast - ema_slow
    df_macd['Signal'] = df_macd['MACD'].ewm(span=signal, adjust=False).mean()
    df_macd['Histogram'] = df_macd['MACD'] - df_macd['Signal']
    return df_macd

def calculate_rsi(df, period=14):
    df_rsi = df.copy()
    delta = df_rsi['Close Price'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    df_rsi['RSI'] = 100 - (100 / (1 + rs))
    return df_rsi

def get_rsi_signal(df):
    df_rsi = calculate_rsi(df)
    latest_rsi = df_rsi['RSI'].iloc[-1]
    if pd.isna(latest_rsi):
        return None, "Data tidak cukup untuk menghitung RSI", "gray"
    if latest_rsi >= 70:
        return latest_rsi, "🔴 Overbought - Potensi Jual", "red"
    elif latest_rsi <= 30:
        return latest_rsi, "🟢 Oversold - Potensi Beli", "green"
    else:
        return latest_rsi, "⚪ Netral", "gray"