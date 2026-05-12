import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as scipy_stats
from statsmodels.tsa.stattools import acf

from utils.theme import inject_theme, render_hybrid_navbar, get_theme_colors, section_label, page_header
from utils.data_loader import df_map
from utils.visualizations import plot_macd, plot_rsi

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

page_header(title="Exploratory Data Analysis", subtitle="CRISP-DM · Data Understanding")

# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_all():
    return {
        'USD/IDR': df_map['USD/IDR'](),
        'EUR/IDR': df_map['EUR/IDR'](),
        'GBP/IDR': df_map['GBP/IDR'](),
    }

all_data = load_all()

COLOR_MAP = {
    'USD/IDR': '#f0b429',
    'EUR/IDR': '#4d9fff',
    'GBP/IDR': '#a78bfa',
}

# ─────────────────────────────────────────────
# Currency selector
# ─────────────────────────────────────────────
c_sel, _ = st.columns([1, 3])
with c_sel:
    currency = st.selectbox("Currency Pair", list(all_data.keys()), label_visibility="collapsed")

df = all_data[currency].copy()
accent = COLOR_MAP[currency]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _layout(height=450, title=""):
    """Base Plotly layout synced with the current app theme."""
    c = get_theme_colors()
    grid = c['plot_grid']
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=c['plot_bg'],
        font=dict(family="DM Sans", color=c['txt2'], size=11),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=44 if title else 20, b=10),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=c['border'],
            borderwidth=1,
        ),
    )
    if title:
        layout['title'] = dict(text=title, font=dict(size=13, color=c['txt1']), x=0)
    layout['_grid'] = grid  # carry through for axes
    return layout


def _axes(layout, xaxis=None, yaxis=None):
    """Attach xaxis / yaxis overrides after _layout()."""
    grid = layout.pop('_grid', 'rgba(255,255,255,0.04)')
    base_x = dict(showgrid=True, gridcolor=grid, zeroline=False)
    base_y = dict(showgrid=True, gridcolor=grid, zeroline=False)
    if xaxis:
        base_x.update(xaxis)
    if yaxis:
        base_y.update(yaxis)
    layout['xaxis'] = base_x
    layout['yaxis'] = base_y
    return layout


def hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def insight_card(html: str):
    """Styled insight/context card below each section label."""
    c = get_theme_colors()
    st.markdown(
        f"""<div style="background:{c['bg_card']};border:1px solid {c['border_light']};
        border-left:3px solid #00d4aa;border-radius:8px;padding:0.75rem 1rem;
        margin-bottom:0.75rem;font-size:0.82rem;color:{c['txt2']};line-height:1.6;">
        {html}</div>""",
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════
# CHART FUNCTIONS
# ═════════════════════════════════════════════

def plot_price_action(df: pd.DataFrame, color: str) -> go.Figure:
    """
    Interactive OHLC Candlestick chart with an integrated range slider
    so users can zoom into any sub-period without losing the overview.
    """
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close Price'],
        increasing=dict(line=dict(color='#00d4aa'), fillcolor=hex_rgba('#00d4aa', 0.7)),
        decreasing=dict(line=dict(color='#f04b64'), fillcolor=hex_rgba('#f04b64', 0.7)),
        name='OHLC',
        hovertext=None,
    )])

    c = get_theme_colors()
    layout = _layout(height=540, title="Price Action — OHLC Candlestick")
    layout.pop('_grid', None)
    layout['xaxis'] = dict(
        rangeslider=dict(visible=True, thickness=0.07, bgcolor=c['bg_surface']),
        type='date',
        showgrid=True,
        gridcolor=c['plot_grid'],
        zeroline=False,
    )
    layout['yaxis'] = dict(
        title="Price (Rp)",
        showgrid=True,
        gridcolor=c['plot_grid'],
        zeroline=False,
        tickprefix="Rp ",
        tickformat=",.0f",
    )
    fig.update_layout(**layout)
    return fig


def plot_trend_momentum(df: pd.DataFrame, color: str):
    """
    Returns two figures:
      1. Close price overlaid with 20-period and 50-period SMA.
      2. ACF bar plot for lag correlation analysis (lags 0–40).
    """
    close = df['Close Price'].dropna()
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    # — SMA Chart —
    fig_sma = go.Figure()
    fig_sma.add_trace(go.Scatter(
        x=close.index, y=close, name='Close Price',
        line=dict(color=color, width=1), opacity=0.55,
    ))
    fig_sma.add_trace(go.Scatter(
        x=sma20.index, y=sma20, name='SMA-20 (Fast)',
        line=dict(color='#00d4aa', width=1.8),
    ))
    fig_sma.add_trace(go.Scatter(
        x=sma50.index, y=sma50, name='SMA-50 (Slow)',
        line=dict(color='#f04b64', width=1.8, dash='dot'),
    ))
    layout_sma = _layout(height=400, title="Trend — Close Price with 20 & 50-Period Simple Moving Average")
    _axes(layout_sma, yaxis=dict(title="Price (Rp)", tickprefix="Rp ", tickformat=",.0f"))
    fig_sma.update_layout(**layout_sma)

    # — ACF Chart —
    nlags = 40
    acf_vals = acf(close, nlags=nlags, fft=True)
    lags = np.arange(0, nlags + 1)
    ci = 1.96 / np.sqrt(len(close))   # 95 % confidence interval

    fig_acf = go.Figure()
    # Vertical stems — teal for significant, muted for not
    for lag, val in zip(lags, acf_vals):
        bar_color = '#00d4aa' if abs(val) > ci else '#3c506e'
        fig_acf.add_shape(
            type='line',
            x0=lag, x1=lag, y0=0, y1=val,
            line=dict(color=bar_color, width=3),
        )
    fig_acf.add_trace(go.Scatter(
        x=lags, y=acf_vals, mode='markers',
        marker=dict(size=6, color='#00d4aa', line=dict(color='#007a60', width=1)),
        name='ACF value', showlegend=False,
    ))
    # Confidence band lines
    fig_acf.add_hline(y=ci,  line_dash='dash', line_color='#f0b429', line_width=1.2,
                       annotation_text=" +95% CI", annotation_position="right")
    fig_acf.add_hline(y=-ci, line_dash='dash', line_color='#f0b429', line_width=1.2,
                       annotation_text=" −95% CI", annotation_position="right")
    fig_acf.add_hline(y=0,   line_color='#7a90b0', line_width=0.5)

    layout_acf = _layout(height=320, title="Momentum — Autocorrelation Function (ACF), Lags 0–40")
    _axes(layout_acf,
          xaxis=dict(title="Lag (days)", showgrid=False, dtick=5),
          yaxis=dict(title="Autocorrelation", range=[-0.4, 1.05]))
    layout_acf['showlegend'] = False
    fig_acf.update_layout(**layout_acf)

    return fig_sma, fig_acf


def plot_volatility(df: pd.DataFrame, color: str):
    """
    Returns two figures:
      1. Bollinger Bands (20-period SMA ± 2σ) with shaded band area.
      2. 30-day rolling standard deviation of daily returns.
    """
    close = df['Close Price'].dropna()
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = (sma20 + 2 * std20).dropna()
    lower = (sma20 - 2 * std20).dropna()
    common_idx = upper.index  # upper/lower share the same NaN-dropped index

    # — Bollinger Bands —
    fig_bb = go.Figure()
    # Shaded area between bands (polygon trick)
    fig_bb.add_trace(go.Scatter(
        x=list(upper.index) + list(lower.index[::-1]),
        y=list(upper.values) + list(lower.values[::-1]),
        fill='toself',
        fillcolor=hex_rgba('#4d9fff', 0.08),
        line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip',
        showlegend=False,
        name='Band Area',
    ))
    fig_bb.add_trace(go.Scatter(
        x=upper.index, y=upper, name='Upper Band (+2σ)',
        line=dict(color='#4d9fff', width=1, dash='dash'),
    ))
    fig_bb.add_trace(go.Scatter(
        x=lower.index, y=lower, name='Lower Band (−2σ)',
        line=dict(color='#4d9fff', width=1, dash='dash'),
    ))
    fig_bb.add_trace(go.Scatter(
        x=sma20.dropna().index, y=sma20.dropna(), name='SMA-20 (Mid)',
        line=dict(color='#00d4aa', width=1.8),
    ))
    fig_bb.add_trace(go.Scatter(
        x=close.index, y=close, name='Close Price',
        line=dict(color=color, width=1), opacity=0.55,
    ))
    layout_bb = _layout(height=440, title="Volatility — Bollinger Bands (20-period SMA, ±2 Std Dev)")
    _axes(layout_bb, yaxis=dict(title="Price (Rp)", tickprefix="Rp ", tickformat=",.0f"))
    fig_bb.update_layout(**layout_bb)

    # — Rolling Std of Daily Returns —
    daily_ret = close.pct_change()
    roll_std = (daily_ret.rolling(30).std() * 100).dropna()

    fig_rstd = go.Figure()
    fig_rstd.add_trace(go.Scatter(
        x=roll_std.index, y=roll_std,
        mode='lines', name='30-Day Rolling Std',
        line=dict(color='#f04b64', width=1.5),
        fill='tozeroy', fillcolor=hex_rgba('#f04b64', 0.1),
    ))
    layout_rstd = _layout(height=280, title="30-Day Rolling Std Dev of Daily Returns (%)")
    _axes(layout_rstd, yaxis=dict(title="Std Dev (%)"))
    fig_rstd.update_layout(**layout_rstd)

    return fig_bb, fig_rstd


def plot_distribution(df: pd.DataFrame, color: str):
    """
    Returns two figures:
      1. Histogram of daily returns with KDE overlay and normal reference curve.
      2. Box plot of returns grouped by day of the week.
    """
    close = df['Close Price'].dropna()
    returns = (close.pct_change().dropna() * 100)

    # — Histogram + KDE —
    x_vals = np.linspace(returns.min(), returns.max(), 400)
    bin_width = (returns.max() - returns.min()) / 60
    scale = len(returns) * bin_width

    kde = scipy_stats.gaussian_kde(returns)
    kde_curve = kde(x_vals) * scale

    mu, sigma = returns.mean(), returns.std()
    norm_curve = scipy_stats.norm.pdf(x_vals, mu, sigma) * scale

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=returns, nbinsx=60, name='Daily Returns',
        marker_color=color, opacity=0.45,
    ))
    fig_hist.add_trace(go.Scatter(
        x=x_vals, y=kde_curve, mode='lines', name='KDE (actual)',
        line=dict(color='#00d4aa', width=2.5),
    ))
    fig_hist.add_trace(go.Scatter(
        x=x_vals, y=norm_curve, mode='lines', name='Normal Fit',
        line=dict(color='#f0b429', width=1.5, dash='dash'),
    ))
    layout_hist = _layout(height=400, title="Distribution — Daily Returns Histogram with KDE Overlay")
    _axes(layout_hist,
          xaxis=dict(title="Daily Return (%)"),
          yaxis=dict(title="Frequency"))
    layout_hist['bargap'] = 0.02
    fig_hist.update_layout(**layout_hist)

    # — Day-of-Week Box Plot —
    ret_df = returns.rename('Return').to_frame()
    ret_df['Day'] = returns.index.day_name()
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    ret_df = ret_df[ret_df['Day'].isin(weekdays)]

    day_colors = ['#f0b429', '#4d9fff', '#00d4aa', '#a78bfa', '#f04b64']
    fig_box = go.Figure()
    for day, dcolor in zip(weekdays, day_colors):
        vals = ret_df.loc[ret_df['Day'] == day, 'Return']
        fig_box.add_trace(go.Box(
            y=vals, name=day,
            marker_color=dcolor,
            fillcolor=hex_rgba(dcolor, 0.15),
            line=dict(color=dcolor),
            boxmean='sd',
        ))
    layout_box = _layout(height=380, title="Seasonality — Daily Returns by Day of the Week")
    _axes(layout_box, yaxis=dict(title="Daily Return (%)"))
    layout_box['showlegend'] = False
    fig_box.update_layout(**layout_box)

    return fig_hist, fig_box


# ═════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Price Action",
    "📈 Trend & Momentum",
    "🌊 Volatility",
    "📐 Distribution & Stationarity",
    "📉 Technical Indicators",
])

# ─────────────────────────────────────────────
# TAB 1 — Price Action
# ─────────────────────────────────────────────
with tab1:
    insight_card(
        "<b>What you're seeing:</b> An OHLC (Open-High-Low-Close) Candlestick chart showing each trading day's "
        "full price range. <b>Green candles</b> mean the price closed <i>higher</i> than it opened (bullish); "
        "<b>red candles</b> mean it closed <i>lower</i> (bearish). Use the <b>range slider below the chart</b> "
        "to zoom into any specific time window without losing the broader context."
    )
    section_label("Interactive Candlestick — OHLC Price Chart")
    fig_action = plot_price_action(df, accent)
    st.plotly_chart(fig_action, use_container_width=True, config={"displayModeBar": True})

# ─────────────────────────────────────────────
# TAB 2 — Trend & Momentum
# ─────────────────────────────────────────────
with tab2:
    insight_card(
        "<b>What you're seeing:</b> The SMA chart overlays a <b>20-period SMA</b> (fast, reacts quickly) and a "
        "<b>50-period SMA</b> (slow, reflects the longer-term trend). When SMA-20 crosses <i>above</i> SMA-50 "
        "it is called a <i>Golden Cross</i> — historically a bullish signal. The opposite is a <i>Death Cross</i>."
    )
    section_label("Close Price with 20 & 50-Period Simple Moving Average")
    fig_sma, fig_acf = plot_trend_momentum(df, accent)
    st.plotly_chart(fig_sma, use_container_width=True, config={"displayModeBar": False})

    st.markdown("")
    section_label("Autocorrelation Function (ACF) — How Much Does Today's Price Depend on the Past?")
    insight_card(
        "<b>How to read ACF:</b> Each bar shows the correlation between today's price and the price <i>N days ago</i> "
        "(Lag N). Bars that exceed the <b>yellow dashed ±95% confidence bands</b> are statistically significant — "
        "the price genuinely 'remembers' what happened N days before. For raw forex prices, you will typically see "
        "all lags highly significant, confirming the series is <b>non-stationary</b>. ARIMA-family models handle this "
        "by differencing the series before fitting."
    )
    st.plotly_chart(fig_acf, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────
# TAB 3 — Volatility
# ─────────────────────────────────────────────
with tab3:
    insight_card(
        "<b>What you're seeing:</b> <b>Bollinger Bands</b> are built from a 20-period SMA plus/minus 2 standard "
        "deviations. The <b>shaded blue area</b> between the upper and lower bands visualises current volatility — "
        "wider bands = higher volatility, narrower bands = lower volatility (a <i>squeeze</i> that often precedes "
        "a breakout). Prices touching or crossing the outer bands can signal overbought/oversold conditions."
    )
    section_label("Bollinger Bands — 20-Period SMA ± 2 Standard Deviations")
    fig_bb, fig_rstd = plot_volatility(df, accent)
    st.plotly_chart(fig_bb, use_container_width=True, config={"displayModeBar": False})

    st.markdown("")
    section_label("30-Day Rolling Std Dev of Daily Returns — Recent Market Risk")
    insight_card(
        "<b>How to read this chart:</b> This is the 30-day rolling standard deviation of daily percentage returns. "
        "Think of it as a real-time <i>risk gauge</i>: <b>spikes</b> correspond to periods of high turbulence "
        "(e.g., economic shocks, geopolitical events, central bank announcements). For forecasting, knowing that "
        "the model is operating inside a high-volatility regime helps calibrate how wide the prediction intervals "
        "should be."
    )
    st.plotly_chart(fig_rstd, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────
# TAB 4 — Distribution & Stationarity
# ─────────────────────────────────────────────
with tab4:
    insight_card(
        "<b>What you're seeing:</b> The histogram shows how often each return size actually occurred. "
        "The <b>green KDE line</b> is a smooth, non-parametric estimate of the true return distribution; "
        "the <b>dashed yellow line</b> shows what a perfect normal distribution would look like given the same "
        "mean and standard deviation. If the KDE shows <i>fat tails</i> (the distribution extends further than "
        "the normal curve), it means extreme moves happen more frequently than classical statistics predicts — "
        "a well-known feature of financial return series called <i>leptokurtosis</i>."
    )
    section_label("Daily Returns — Histogram with KDE and Normal Reference Curve")
    fig_hist, fig_box = plot_distribution(df, accent)
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

    st.markdown("")
    section_label("Calendar Seasonality — Daily Returns by Day of the Week")
    insight_card(
        "<b>How to read this chart:</b> Each box represents the distribution of daily returns for one weekday. "
        "The <b>horizontal line</b> inside the box is the median; the box itself spans the interquartile range (IQR); "
        "the diamond inside is the mean, and the whisker extension shows the standard deviation. "
        "If any day shows a consistently different median or spread, it is evidence of <i>weekly seasonality</i> — "
        "useful context when interpreting model errors that cluster on specific days."
    )
    st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────
# TAB 5 — Technical Indicators
# ─────────────────────────────────────────────
_TA_RANGE = {
    "1D": 1, "1W": 7, "1M": 30, "3M": 90,
    "1Y": 365, "3Y": 1095, "5Y": 1825, "All": 99999,
}

with tab5:
    # Time range selector — same style as Prediction page
    r_col, _ = st.columns([2, 4])
    with r_col:
        ta_label = st.selectbox(
            "Time Range", list(_TA_RANGE.keys()), index=3, key="ta_range",
            label_visibility="collapsed",
        )
    ta_n_days = _TA_RANGE[ta_label]

    # ── MACD ──────────────────────────────────
    section_label("MACD — Moving Average Convergence Divergence (12 / 26 / 9)")
    insight_card(
        "<b>What is MACD?</b> MACD measures the momentum behind a price trend by comparing two "
        "exponential moving averages — the <b>12-period EMA</b> minus the <b>26-period EMA</b>. "
        "A 9-period EMA of that result is plotted as the <b>Signal line</b>. "
        "The <b>histogram</b> shows the gap between them: green bars mean momentum is building upward, "
        "red bars mean it is fading or reversing."
        "<br><br>"
        "<b>How to read it:</b><br>"
        "• <b>MACD crosses above Signal</b> → bullish crossover — momentum shifting upward<br>"
        "• <b>MACD crosses below Signal</b> → bearish crossover — momentum shifting downward<br>"
        "• <b>Both lines above zero</b> → overall uptrend; <b>both below zero</b> → overall downtrend<br>"
        "• <b>Histogram shrinking</b> → the current trend is losing steam, possible reversal ahead"
    )
    plot_macd(df, ta_n_days)

    st.markdown("")

    # ── RSI ───────────────────────────────────
    section_label("RSI — Relative Strength Index (14-period)")
    insight_card(
        "<b>What is RSI?</b> RSI is a momentum oscillator that scores recent price strength on a "
        "scale from <b>0 to 100</b>. It answers the question: <i>\"Has this currency moved too far, "
        "too fast?\"</i> — helping spot potential turning points before they happen."
        "<br><br>"
        "<b>How to read it:</b><br>"
        "• <b>RSI above 70 (red zone)</b> → Overbought — the price has risen sharply and may be "
        "due for a pullback or consolidation<br>"
        "• <b>RSI below 30 (green zone)</b> → Oversold — the price has fallen sharply and may be "
        "due for a bounce or recovery<br>"
        "• <b>RSI around 50</b> → Neutral — no strong momentum signal in either direction<br>"
        "• <b>Divergence</b>: if the price makes a new high but RSI does not, that is a warning sign "
        "that the uptrend may be weakening"
    )
    plot_rsi(df, ta_n_days)
