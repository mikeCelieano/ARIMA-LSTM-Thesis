import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose

from utils.theme import inject_theme, render_hybrid_navbar

inject_theme()
render_hybrid_navbar(show_prediction_controls=False)

# Helper functions
def page_header(title, subtitle=""):
    st.markdown(f"<h1 style='margin-bottom:0.2rem;'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color:#7a90b0;font-size:0.85rem;margin-top:0;'>{subtitle}</p>", unsafe_allow_html=True)

def section_label(text):
    st.markdown(f"**{text}**")

page_header(title="Exploratory Data Analysis", subtitle="CRISP-DM: Data Understanding")

# ─────────────────────────────────────────────
# Load all currencies + macro data
# ─────────────────────────────────────────────
from utils.data_loader import df_map, combine_exog

@st.cache_data(ttl=3600)
def load_all_data():
    usd = df_map['USD/IDR']()
    eur = df_map['EUR/IDR']()
    gbp = df_map['GBP/IDR']()
    exog = combine_exog()
    
    # Merge on index
    combined = pd.DataFrame({
        'USD': usd['Close Price'],
        'EUR': eur['Close Price'],
        'GBP': gbp['Close Price'],
    })
    combined = combined.join(exog, how='left').ffill().bfill()
    
    return usd, eur, gbp, combined

usd_df, eur_df, gbp_df, combined_df = load_all_data()

# Shared Plotly theme (no xaxis/yaxis here to avoid conflicts)
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1421",
    font=dict(family="DM Sans", color="#7a90b0", size=11),
    hovermode="x unified", margin=dict(l=10, r=10, t=40, b=10),
)

# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tabs = st.tabs([
    "📊 Data Overview",
    "📈 Distribution Analysis", 
    "🔄 Time Series Patterns",
    "🔗 Correlation Analysis",
    "⚠️ Volatility & Risk",
    "🏦 Macroeconomic Impact"
])

# ═════════════════════════════════════════════
# TAB 1: Data Overview
# ═════════════════════════════════════════════
with tabs[0]:
    section_label("Summary Statistics")
    
    # Summary table
    summary_data = []
    for name, df in [('USD/IDR', usd_df), ('EUR/IDR', eur_df), ('GBP/IDR', gbp_df)]:
        summary_data.append({
            'Currency': name,
            'Count': len(df),
            'Mean': df['Close Price'].mean(),
            'Std': df['Close Price'].std(),
            'Min': df['Close Price'].min(),
            'Max': df['Close Price'].max(),
            'Latest': df['Close Price'].iloc[-1],
            'Start Date': df.index.min().strftime('%Y-%m-%d'),
            'End Date': df.index.max().strftime('%Y-%m-%d'),
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df['Mean'] = summary_df['Mean'].apply(lambda x: f"Rp {x:,.2f}")
    summary_df['Std'] = summary_df['Std'].apply(lambda x: f"Rp {x:,.2f}")
    summary_df['Min'] = summary_df['Min'].apply(lambda x: f"Rp {x:,.2f}")
    summary_df['Max'] = summary_df['Max'].apply(lambda x: f"Rp {x:,.2f}")
    summary_df['Latest'] = summary_df['Latest'].apply(lambda x: f"Rp {x:,.2f}")
    
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.write("")
    section_label("Data Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    # Missing values
    total_possible = len(pd.date_range(combined_df.index.min(), combined_df.index.max(), freq='D'))
    missing_usd = total_possible - len(usd_df)
    missing_eur = total_possible - len(eur_df)
    missing_gbp = total_possible - len(gbp_df)
    
    col1.metric("USD/IDR Coverage", f"{len(usd_df):,} days", f"-{missing_usd} missing")
    col2.metric("EUR/IDR Coverage", f"{len(eur_df):,} days", f"-{missing_eur} missing")
    col3.metric("GBP/IDR Coverage", f"{len(gbp_df):,} days", f"-{missing_gbp} missing")
    
    st.write("")
    section_label("Date Range Coverage")
    
    fig = go.Figure()
    for name, df, color in [
        ('USD/IDR', usd_df, '#f0b429'),
        ('EUR/IDR', eur_df, '#4d9fff'),
        ('GBP/IDR', gbp_df, '#a78bfa')
    ]:
        fig.add_trace(go.Scatter(
            x=[df.index.min(), df.index.max()],
            y=[name, name],
            mode='lines+markers',
            name=name,
            line=dict(color=color, width=8),
            marker=dict(size=12, color=color),
        ))
    
    layout = {**_LAYOUT, 'height': 250, 'showlegend': False}
    layout['yaxis'] = dict(title="", showgrid=False)
    layout['xaxis'] = dict(title="Date Range", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═════════════════════════════════════════════
# TAB 2: Distribution Analysis
# ═════════════════════════════════════════════
with tabs[1]:
    section_label("Price Distribution")
    
    fig = make_subplots(rows=1, cols=3, subplot_titles=['USD/IDR', 'EUR/IDR', 'GBP/IDR'])
    
    for idx, (df, color) in enumerate([
        (usd_df, '#f0b429'), (eur_df, '#4d9fff'), (gbp_df, '#a78bfa')
    ], start=1):
        fig.add_trace(
            go.Histogram(x=df['Close Price'], nbinsx=50, marker_color=color, 
                         name='', showlegend=False, opacity=0.75),
            row=1, col=idx
        )
    
    fig.update_layout(**_LAYOUT, height=350, showlegend=False)
    fig.update_xaxes(title_text="Price (Rp)")
    fig.update_yaxes(title_text="Frequency")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Daily Returns Distribution")
    
    fig = make_subplots(rows=1, cols=3, subplot_titles=['USD/IDR', 'EUR/IDR', 'GBP/IDR'])
    
    for idx, (df, color) in enumerate([
        (usd_df, '#f0b429'), (eur_df, '#4d9fff'), (gbp_df, '#a78bfa')
    ], start=1):
        returns = df['Close Price'].pct_change().dropna() * 100
        
        fig.add_trace(
            go.Histogram(x=returns, nbinsx=60, marker_color=color,
                         name='', showlegend=False, opacity=0.75),
            row=1, col=idx
        )
        
        # Add normal distribution overlay
        mu, sigma = returns.mean(), returns.std()
        x_range = np.linspace(returns.min(), returns.max(), 100)
        y_normal = stats.norm.pdf(x_range, mu, sigma) * len(returns) * (returns.max() - returns.min()) / 60
        
        fig.add_trace(
            go.Scatter(x=x_range, y=y_normal, mode='lines',
                       line=dict(color='#00d4aa', width=2, dash='dash'),
                       name='Normal', showlegend=(idx==1)),
            row=1, col=idx
        )
    
    fig.update_layout(**_LAYOUT, height=350)
    fig.update_xaxes(title_text="Daily Returns (%)")
    fig.update_yaxes(title_text="Frequency")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Outlier Detection (Box Plot)")
    
    fig = go.Figure()
    for name, df, color in [
        ('USD/IDR', usd_df, '#f0b429'),
        ('EUR/IDR', eur_df, '#4d9fff'),
        ('GBP/IDR', gbp_df, '#a78bfa')
    ]:
        returns = df['Close Price'].pct_change().dropna() * 100
        fig.add_trace(go.Box(y=returns, name=name, marker_color=color, boxmean='sd'))
    
    layout = {**_LAYOUT, 'height': 400, 'showlegend': True}
    layout['yaxis'] = dict(title="Daily Returns (%)", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═════════════════════════════════════════════
# TAB 3: Time Series Patterns
# ═════════════════════════════════════════════
with tabs[2]:
    currency_choice = st.radio("Select Currency", ['USD/IDR', 'EUR/IDR', 'GBP/IDR'], horizontal=True)
    
    df_selected = {'USD/IDR': usd_df, 'EUR/IDR': eur_df, 'GBP/IDR': gbp_df}[currency_choice]
    color_map = {'USD/IDR': '#f0b429', 'EUR/IDR': '#4d9fff', 'GBP/IDR': '#a78bfa'}[currency_choice]
    
    section_label("Trend Decomposition (Additive)")
    
    # Decompose
    decomp = seasonal_decompose(
        df_selected['Close Price'].dropna(), 
        model='additive', 
        period=30,  # Monthly seasonality
        extrapolate_trend='freq'
    )
    
    fig = make_subplots(rows=4, cols=1, 
                        subplot_titles=['Original', 'Trend', 'Seasonal', 'Residual'],
                        vertical_spacing=0.08)
    
    fig.add_trace(go.Scatter(x=decomp.observed.index, y=decomp.observed, 
                             line=dict(color=color_map, width=1), name='Original'), row=1, col=1)
    fig.add_trace(go.Scatter(x=decomp.trend.index, y=decomp.trend,
                             line=dict(color='#00d4aa', width=1.5), name='Trend'), row=2, col=1)
    fig.add_trace(go.Scatter(x=decomp.seasonal.index, y=decomp.seasonal,
                             line=dict(color='#4d9fff', width=1), name='Seasonal'), row=3, col=1)
    fig.add_trace(go.Scatter(x=decomp.resid.index, y=decomp.resid,
                             line=dict(color='#f04b64', width=0.8), name='Residual'), row=4, col=1)
    
    fig.update_layout(**_LAYOUT, height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Rolling Statistics (30/90/365-Day Moving Averages)")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_selected.index, y=df_selected['Close Price'],
                             mode='lines', name='Close Price', line=dict(color='#7a90b0', width=1)))
    
    for window, color, name in [(30, '#f0b429', '30-Day MA'), 
                                  (90, '#4d9fff', '90-Day MA'),
                                  (365, '#00d4aa', '365-Day MA')]:
        ma = df_selected['Close Price'].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=ma.index, y=ma, mode='lines', name=name,
                                 line=dict(color=color, width=1.5)))
    
    layout = {**_LAYOUT, 'height': 400}
    layout['yaxis'] = dict(title="Price (Rp)", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Rolling Volatility (30-Day)")
    
    rolling_std = df_selected['Close Price'].pct_change().rolling(window=30).std() * 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rolling_std.index, y=rolling_std,
                             mode='lines', name='30-Day Rolling Volatility',
                             line=dict(color='#f04b64', width=1.5),
                             fill='tozeroy', fillcolor='rgba(240,75,100,0.1)'))
    
    layout = {**_LAYOUT, 'height': 350}
    layout['yaxis'] = dict(title="Volatility (%)", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═════════════════════════════════════════════
# TAB 4: Correlation Analysis
# ═════════════════════════════════════════════
with tabs[3]:
    section_label("Correlation Matrix (All Variables)")
    
    corr_matrix = combined_df[['USD', 'EUR', 'GBP', 'Inflasi', 'BI Rate']].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale=[
            [0, '#f04b64'], [0.5, '#0d1421'], [1, '#00d4aa']
        ],
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 12, "color": "#dce8f7"},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(**_LAYOUT, height=450)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Pairwise Scatter Matrix")
    
    # Scatter matrix
    fig = make_subplots(rows=3, cols=3, 
                        subplot_titles=['USD vs EUR', 'USD vs GBP', 'EUR vs GBP',
                                        'USD vs BI Rate', 'EUR vs BI Rate', 'GBP vs BI Rate',
                                        'USD vs Inflasi', 'EUR vs Inflasi', 'GBP vs Inflasi'])
    
    pairs = [
        ('USD', 'EUR', '#f0b429'), ('USD', 'GBP', '#4d9fff'), ('EUR', 'GBP', '#a78bfa'),
        ('USD', 'BI Rate', '#f0b429'), ('EUR', 'BI Rate', '#4d9fff'), ('GBP', 'BI Rate', '#a78bfa'),
        ('USD', 'Inflasi', '#f0b429'), ('EUR', 'Inflasi', '#4d9fff'), ('GBP', 'Inflasi', '#a78bfa'),
    ]
    
    for idx, (x_col, y_col, color) in enumerate(pairs, start=1):
        row = (idx - 1) // 3 + 1
        col = (idx - 1) % 3 + 1
        
        fig.add_trace(go.Scatter(
            x=combined_df[x_col], y=combined_df[y_col],
            mode='markers', marker=dict(size=3, color=color, opacity=0.4),
            showlegend=False
        ), row=row, col=col)
    
    fig.update_layout(**_LAYOUT, height=650, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═════════════════════════════════════════════
# TAB 5: Volatility & Risk
# ═════════════════════════════════════════════
with tabs[4]:
    section_label("Historical Volatility Comparison")
    
    fig = go.Figure()
    for name, df, color in [
        ('USD/IDR', usd_df, '#f0b429'),
        ('EUR/IDR', eur_df, '#4d9fff'),
        ('GBP/IDR', gbp_df, '#a78bfa')
    ]:
        vol = df['Close Price'].pct_change().rolling(window=30).std() * 100 * np.sqrt(252)
        fig.add_trace(go.Scatter(x=vol.index, y=vol, mode='lines', name=name,
                                 line=dict(color=color, width=1.5)))
    
    layout = {**_LAYOUT, 'height': 400}
    layout['yaxis'] = dict(title="Annualized Volatility (%)", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Value at Risk (VaR) - 95% Confidence")
    
    var_data = []
    for name, df in [('USD/IDR', usd_df), ('EUR/IDR', eur_df), ('GBP/IDR', gbp_df)]:
        returns = df['Close Price'].pct_change().dropna() * 100
        var_95 = np.percentile(returns, 5)
        var_data.append({'Currency': name, 'VaR (95%)': f"{var_95:.4f}%"})
    
    var_df = pd.DataFrame(var_data)
    st.dataframe(var_df, use_container_width=True, hide_index=True)
    
    st.write("")
    section_label("Daily High-Low Spread Over Time")
    
    fig = go.Figure()
    for name, df, color in [
        ('USD/IDR', usd_df, '#f0b429'),
        ('EUR/IDR', eur_df, '#4d9fff'),
        ('GBP/IDR', gbp_df, '#a78bfa')
    ]:
        spread = ((df['High'] - df['Low']) / df['Close Price']) * 100
        fig.add_trace(go.Scatter(x=spread.index, y=spread.rolling(30).mean(),
                                 mode='lines', name=name, line=dict(color=color, width=1.5)))
    
    layout = {**_LAYOUT, 'height': 350}
    layout['yaxis'] = dict(title="Avg Daily Spread (%)", showgrid=True, gridcolor="rgba(255,255,255,0.04)")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═════════════════════════════════════════════
# TAB 6: Macroeconomic Impact
# ═════════════════════════════════════════════
with tabs[5]:
    section_label("Forex vs BI Rate")
    
    fig = make_subplots(rows=1, cols=3, subplot_titles=['USD/IDR', 'EUR/IDR', 'GBP/IDR'])
    
    for idx, (col, color) in enumerate([('USD', '#f0b429'), ('EUR', '#4d9fff'), ('GBP', '#a78bfa')], start=1):
        fig.add_trace(go.Scatter(
            x=combined_df['BI Rate'], y=combined_df[col],
            mode='markers', marker=dict(size=3, color=color, opacity=0.5),
            showlegend=False
        ), row=1, col=idx)
    
    fig.update_layout(**_LAYOUT, height=350)
    fig.update_xaxes(title_text="BI Rate (%)")
    fig.update_yaxes(title_text="Forex Rate (Rp)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Forex vs Inflation")
    
    fig = make_subplots(rows=1, cols=3, subplot_titles=['USD/IDR', 'EUR/IDR', 'GBP/IDR'])
    
    for idx, (col, color) in enumerate([('USD', '#f0b429'), ('EUR', '#4d9fff'), ('GBP', '#a78bfa')], start=1):
        fig.add_trace(go.Scatter(
            x=combined_df['Inflasi'], y=combined_df[col],
            mode='markers', marker=dict(size=3, color=color, opacity=0.5),
            showlegend=False
        ), row=1, col=idx)
    
    fig.update_layout(**_LAYOUT, height=350)
    fig.update_xaxes(title_text="Inflation (%)")
    fig.update_yaxes(title_text="Forex Rate (Rp)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.write("")
    section_label("Rolling Correlation: Forex vs Macro Variables (90-Day Window)")
    
    fig = make_subplots(rows=2, cols=1, subplot_titles=['Forex vs BI Rate', 'Forex vs Inflation'])
    
    for col, color, name in [('USD', '#f0b429', 'USD/IDR'), ('EUR', '#4d9fff', 'EUR/IDR'), ('GBP', '#a78bfa', 'GBP/IDR')]:
        corr_bi = combined_df[col].rolling(90).corr(combined_df['BI Rate'])
        corr_inf = combined_df[col].rolling(90).corr(combined_df['Inflasi'])
        
        fig.add_trace(go.Scatter(x=corr_bi.index, y=corr_bi, mode='lines', name=name,
                                 line=dict(color=color, width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=corr_inf.index, y=corr_inf, mode='lines', name=name,
                                 line=dict(color=color, width=1.5), showlegend=False), row=2, col=1)
    
    fig.update_layout(**_LAYOUT, height=500)
    fig.update_yaxes(title_text="Correlation", row=1, col=1)
    fig.update_yaxes(title_text="Correlation", row=2, col=1)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})