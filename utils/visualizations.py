import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from utils.indicators import calculate_macd, calculate_rsi

# ─────────────────────────────────────────────
# Shared dark Plotly layout — SMOOTH version
# (spike lines removed → smooth pan/zoom)
# ─────────────────────────────────────────────
_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d1421",
    font=dict(family="DM Sans, sans-serif", color="#7a90b0", size=11),
    xaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)", gridwidth=1,
        linecolor="rgba(255,255,255,0.06)", zeroline=False,
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#4a6080"),
        rangeslider=dict(visible=False),
        fixedrange=False,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)", gridwidth=1,
        linecolor="rgba(255,255,255,0.06)", zeroline=False,
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#4a6080"),
        fixedrange=False,
    ),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#121c30",
        bordercolor="rgba(0,212,170,0.25)",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#dce8f7"),
    ),
    legend=dict(
        bgcolor="rgba(13,20,33,0.85)",
        bordercolor="rgba(255,255,255,0.06)",
        borderwidth=1,
        font=dict(family="DM Sans, sans-serif", size=11, color="#7a90b0"),
    ),
    margin=dict(l=10, r=10, t=40, b=10),
    dragmode='pan',
)

_INTERACTIVE_CFG = {
    "displayModeBar": True,
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "forex_chart",
        "height": 800,
        "width": 1200,
        "scale": 2,
    },
    "doubleClick": "reset",
}

_STATIC_CFG = {"displayModeBar": False}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _initial_window(df: pd.DataFrame, n_days: int, y_col: str = None,
                    y_low_col: str = None, y_high_col: str = None):
    """Return initial visible (x_range, y_range) — pakai full data, set view awal."""
    if n_days >= 99999:
        return None, None

    end = df.index.max()
    start = end - pd.Timedelta(days=n_days)
    df_visible = df.loc[df.index >= start]

    if df_visible.empty:
        return None, None

    if y_low_col and y_high_col:
        y_min = df_visible[y_low_col].min()
        y_max = df_visible[y_high_col].max()
    elif y_col:
        y_min = df_visible[y_col].min()
        y_max = df_visible[y_col].max()
    else:
        return [start, end], None

    pad = (y_max - y_min) * 0.08
    return [start, end], [y_min - pad, y_max + pad]


def _resample_ohlc(df: pd.DataFrame, max_bars: int = 500):
    """Auto-resample OHLC kalau terlalu banyak bar → smooth pan/zoom."""
    if len(df) <= max_bars:
        return df, ""

    ratio = len(df) / max_bars
    if ratio <= 2:
        freq, label = 'B', ""
    elif ratio <= 7:
        freq, label = 'W', " · weekly"
    elif ratio <= 30:
        freq, label = 'ME', " · monthly"
    else:
        freq, label = 'QE', " · quarterly"

    df_r = df.resample(freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close Price': 'last',
    }).dropna()
    return df_r, label


def _title_annotation(text: str) -> dict:
    return dict(
        text=text, x=0.0, xanchor="left",
        font=dict(family="Syne, sans-serif", size=13, color="#dce8f7"),
    )


# ─────────────────────────────────────────────
# Forex Prediction Chart
# ─────────────────────────────────────────────
def plot_forex_interactive(df_inf, res, currency, n_days=30):
    last_date = df_inf.index[-1].replace(tzinfo=None)
    last_price = df_inf['Close Price'].iloc[-1]

    r_date_raw = res.get('Date') or res.get('date')
    if r_date_raw is not None:
        r_date = pd.to_datetime(r_date_raw).replace(tzinfo=None)
        if r_date <= last_date:
            r_date = last_date + pd.Timedelta(days=1)
    else:
        r_date = last_date + pd.Timedelta(days=1)

    r_upper = res.get('Upper CI') or res.get('upper_ci')
    r_lower = res.get('Lower CI') or res.get('lower_ci')
    r_next  = res.get('Forecast') or res.get('next_price')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[last_date, r_date, r_date, last_date],
        y=[last_price, r_upper, r_lower, last_price],
        fill='toself', fillcolor='rgba(0, 212, 170, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name="95% CI", hoverinfo='skip'
    ))

    fig.add_trace(go.Scatter(
        x=df_inf.index, y=df_inf["Close Price"],
        mode="lines", name="Historical Price",
        line=dict(color="#4d9fff", width=2),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Price: Rp %{y:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=[last_date, r_date], y=[last_price, r_next],
        mode="lines+markers", name="Prediction",
        line=dict(color="#00d4aa", width=2, dash="dash"),
        marker=dict(color="#00d4aa", size=10, symbol="diamond",
                    line=dict(color="#070b12", width=1)),
        hovertemplate="<b>Prediction</b><br>%{x|%d %b %Y}<br>Rp %{y:,.2f}<extra></extra>"
    ))

    if n_days < 99999:
        start_date = last_date - pd.Timedelta(days=n_days)
        df_visible = df_inf.loc[df_inf.index >= start_date]
        y_min = min(df_visible["Close Price"].min(), r_lower)
        y_max = max(df_visible["Close Price"].max(), r_upper)
        pad = (y_max - y_min) * 0.08
        x_range = [start_date, r_date + pd.Timedelta(days=1)]
        y_range = [y_min - pad, y_max + pad]
    else:
        x_range = [df_inf.index.min(), r_date + pd.Timedelta(days=1)]
        y_range = None

    fig.update_layout(**{
        **_BASE_LAYOUT,
        "height": 500,
        "xaxis": dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.03)",
            range=x_range, fixedrange=False,
        ),
        "yaxis": dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.03)",
            side="right", tickformat=",.0f",
            range=y_range, fixedrange=False,
        ),
        "showlegend": True,
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    })
    return fig


# ─────────────────────────────────────────────
# Candlestick — with auto-resample for smoothness
# ─────────────────────────────────────────────
def plot_candlestick(df: pd.DataFrame, n_days: int, currency_label: str = ""):
    df_plot, freq_label = _resample_ohlc(df, max_bars=500)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot["Open"], high=df_plot["High"],
        low=df_plot["Low"], close=df_plot["Close Price"],
        name="OHLC",
        increasing=dict(line=dict(color="#00d4aa", width=1), fillcolor="#00d4aa"),
        decreasing=dict(line=dict(color="#f04b64", width=1), fillcolor="#f04b64"),
        whiskerwidth=0.5,
    ))

    x_range, y_range = _initial_window(df_plot, n_days,
                                       y_low_col="Low", y_high_col="High")

    xaxis_cfg = {**_BASE_LAYOUT["xaxis"], "rangeslider": dict(visible=False)}
    if x_range: xaxis_cfg["range"] = x_range
    yaxis_cfg = {**_BASE_LAYOUT["yaxis"]}
    if y_range: yaxis_cfg["range"] = y_range

    layout = {**_BASE_LAYOUT, "height": 420,
              "title": _title_annotation(f"{currency_label}  —  Candlestick{freq_label}"),
              "xaxis": xaxis_cfg, "yaxis": yaxis_cfg}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config=_INTERACTIVE_CFG)


# ─────────────────────────────────────────────
# Line chart (optionally with forecast overlay)
# ─────────────────────────────────────────────
def plot_line(df: pd.DataFrame, n_days: int,
              currency_label: str = "", df_forecast: pd.DataFrame = None):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close Price"],
        mode="lines", name="Close Price",
        line=dict(color="#4d9fff", width=1.5),
        fill="tozeroy", fillcolor="rgba(77,159,255,0.05)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Close: Rp %{y:,.2f}<extra></extra>",
    ))

    if df_forecast is not None and not df_forecast.empty:
        fig.add_trace(go.Scatter(
            x=list(df_forecast["Date"]) + list(df_forecast["Date"][::-1]),
            y=list(df_forecast["Upper CI"]) + list(df_forecast["Lower CI"][::-1]),
            fill="toself", fillcolor="rgba(0,212,170,0.07)",
            line=dict(color="rgba(0,212,170,0.2)", width=0.5),
            name="95% CI", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=df_forecast["Date"], y=df_forecast["Forecast"],
            mode="markers+lines", name="Forecast",
            line=dict(color="#00d4aa", width=1.5, dash="dash"),
            marker=dict(color="#00d4aa", size=9, symbol="diamond",
                        line=dict(color="#000", width=1)),
            hovertemplate="<b>Forecast: %{x|%d %b %Y}</b><br>Rp %{y:,.2f}<extra></extra>",
        ))

    x_range, y_range = _initial_window(df, n_days, y_col="Close Price")

    xaxis_cfg = {**_BASE_LAYOUT["xaxis"]}
    if x_range: xaxis_cfg["range"] = x_range
    yaxis_cfg = {**_BASE_LAYOUT["yaxis"]}
    if y_range: yaxis_cfg["range"] = y_range

    layout = {**_BASE_LAYOUT, "height": 420,
              "title": _title_annotation(f"{currency_label}  —  Close Price"),
              "xaxis": xaxis_cfg, "yaxis": yaxis_cfg}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config=_INTERACTIVE_CFG)


# ─────────────────────────────────────────────
# MACD chart
# ─────────────────────────────────────────────
def plot_macd(df: pd.DataFrame, n_days: int):
    df_m = calculate_macd(df)

    hist_colors = [
        "rgba(0,212,170,0.65)" if v >= 0 else "rgba(240,75,100,0.65)"
        for v in df_m["Histogram"]
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_m.index, y=df_m["MACD"], mode="lines", name="MACD",
        line=dict(color="#4d9fff", width=1.5),
        hovertemplate="%{x|%d %b}<br>MACD: %{y:.4f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=df_m.index, y=df_m["Signal"], mode="lines", name="Signal",
        line=dict(color="#f0b429", width=1.5),
        hovertemplate="%{x|%d %b}<br>Signal: %{y:.4f}<extra></extra>"))
    fig.add_trace(go.Bar(
        x=df_m.index, y=df_m["Histogram"],
        name="Histogram", marker_color=hist_colors, hoverinfo="skip"))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.08)", width=1, dash="dot"))

    if n_days < 99999:
        end = df_m.index.max()
        start = end - pd.Timedelta(days=n_days)
        df_vis = df_m.loc[df_m.index >= start]
        y_min = min(df_vis["MACD"].min(), df_vis["Signal"].min(), df_vis["Histogram"].min())
        y_max = max(df_vis["MACD"].max(), df_vis["Signal"].max(), df_vis["Histogram"].max())
        pad = (y_max - y_min) * 0.15
        x_range = [start, end]
        y_range = [y_min - pad, y_max + pad]
    else:
        x_range, y_range = None, None

    xaxis_cfg = {**_BASE_LAYOUT["xaxis"]}
    if x_range: xaxis_cfg["range"] = x_range
    yaxis_cfg = {**_BASE_LAYOUT["yaxis"]}
    if y_range: yaxis_cfg["range"] = y_range

    layout = {**_BASE_LAYOUT, "height": 300, "bargap": 0.15,
              "title": _title_annotation("MACD  (12 / 26 / 9)"),
              "xaxis": xaxis_cfg, "yaxis": yaxis_cfg}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config=_INTERACTIVE_CFG)


# ─────────────────────────────────────────────
# RSI chart
# ─────────────────────────────────────────────
def plot_rsi(df: pd.DataFrame, n_days: int, period: int = 14):
    df_r = calculate_rsi(df, period=period)

    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(240,75,100,0.04)", line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,212,170,0.04)",  line_width=0)
    fig.add_trace(go.Scatter(
        x=df_r.index, y=df_r["RSI"], mode="lines", name="RSI",
        line=dict(color="#a78bfa", width=1.5),
        fill="tozeroy", fillcolor="rgba(167,139,250,0.05)",
        hovertemplate="%{x|%d %b}<br>RSI: %{y:.2f}<extra></extra>"))
    fig.add_hline(y=70, line=dict(color="rgba(240,75,100,0.5)", width=1, dash="dash"),
        annotation_text="Overbought (70)", annotation_position="top right",
        annotation_font=dict(color="rgba(240,75,100,0.7)", size=10, family="DM Sans"))
    fig.add_hline(y=30, line=dict(color="rgba(0,212,170,0.5)", width=1, dash="dash"),
        annotation_text="Oversold (30)", annotation_position="bottom right",
        annotation_font=dict(color="rgba(0,212,170,0.7)", size=10, family="DM Sans"))

    x_range, _ = _initial_window(df_r, n_days)

    xaxis_cfg = {**_BASE_LAYOUT["xaxis"]}
    if x_range: xaxis_cfg["range"] = x_range

    layout = {**_BASE_LAYOUT, "height": 280,
              "title": _title_annotation(f"RSI  ({period})"),
              "xaxis": xaxis_cfg,
              "yaxis": {**_BASE_LAYOUT["yaxis"], "range": [0, 100]}}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config=_INTERACTIVE_CFG)


# ─────────────────────────────────────────────
# Timeframe selector
# ─────────────────────────────────────────────
_RANGE_OPTIONS = ["7D", "1M", "3M", "6M", "1Y", "3Y", "5Y", "Max"]
_RANGE_MAP = {
    "7D": 7, "1M": 30, "3M": 90, "6M": 180,
    "1Y": 365, "3Y": 1095, "5Y": 1825, "Max": 99999,
}


def choose_plot_range(default: str = "3M", sidebar: bool = False) -> int:
    if "plot_range" not in st.session_state:
        st.session_state.plot_range = default
    radio = st.sidebar.radio if sidebar else st.radio
    selected = radio(
        "Time Range" if sidebar else "Range",
        _RANGE_OPTIONS, horizontal=True,
        index=_RANGE_OPTIONS.index(st.session_state.plot_range),
        label_visibility="collapsed",
    )
    st.session_state.plot_range = selected
    return _RANGE_MAP[selected]


def choose_sidebar_plot_range(default: str = "3M") -> int:
    return choose_plot_range(default=default, sidebar=True)


# ─────────────────────────────────────────────
# Backward compatibility
# ─────────────────────────────────────────────
def display_side_by_side_metrics(eval_metrics: dict):
    if not eval_metrics:
        st.warning("Evaluation metrics not available.")
        return
    df_m = pd.DataFrame(eval_metrics).T
    df_m["MAE"]         = df_m["MAE"].apply(lambda x: f"Rp {x:,.2f}")
    df_m["RMSE"]        = df_m["RMSE"].apply(lambda x: f"Rp {x:,.2f}")
    df_m["MAPE"]        = df_m["MAPE"].apply(lambda x: f"{x:.2f}%")
    df_m["CI Coverage"] = df_m["CI Coverage"].apply(lambda x: f"{x:.0f}%")
    st.dataframe(df_m, use_container_width=True)


def plot_forex(df_inf, res, currency, n_days=30):
    """Non-interactive version - redirects to interactive"""
    return plot_forex_interactive(df_inf, res, currency, n_days)