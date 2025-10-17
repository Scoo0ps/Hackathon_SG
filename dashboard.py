import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from stock_data.dict_per_stock import get_stock_data
from stock_data.dataframe_percent import get_pct_change_df

# ==========================
# 🎨 CONFIG
# ==========================
st.set_page_config(page_title="SG Market & Sentiment Dashboard", layout="wide")

COLORS = {
    "bg": "#121212",
    "card": "#2A2A2A",
    "inner": "#D9D9D9",
    "text": "#FFFFFF",
    "accent": "#D90429",
    "gray": "#8D99AE",
    "border": "#000000",
    "lightgray": "#BDBDBD"
}

# ==========================
# INIT SESSION STATE
# ==========================
if "view" not in st.session_state:
    st.session_state.view = 1
if "finance_data" not in st.session_state:
    st.session_state.finance_data = {}

# ==========================
# CSS Global
# ==========================
st.markdown(
    f"""
    <style>
    .block-container {{
        padding: 1rem 2rem;
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
    }}
    h1, h2, h3, h4, h5, h6, p, label {{
        color: {COLORS['text']};
    }}
    .stSelectbox, .stRadio > div {{
        background-color: {COLORS['card']};
        color: {COLORS['text']};
        border-radius: 10px;
        padding: 6px 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================
# COMPANY LIST
# ==========================
companies = {
    "AIR.PA": "Airbus SE",
    "BNP.PA": "BNP Paribas SA",
    "SAN.PA": "Sanofi SA",
    "MC.PA": "LVMH SE",
    "OR.PA": "L'Oréal SA",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOG": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc."
}

# ==========================
# HEADER
# ==========================
st.markdown(
    f"""
    <h1 style='color:{COLORS['accent']}; text-align:center; font-size:54px; font-weight:900; margin-bottom:10px;'>
        SG Market & Sentiment Dashboard
    </h1>
    """,
    unsafe_allow_html=True
)

col_mode, _, col_select = st.columns([3, 4, 3])
with col_mode:
    mode = st.radio(
        "Mode selection:",
        ["⚡ Fast & less accurate", "⏳ Slow & more accurate"],
        horizontal=True,
        index=0
    )
with col_select:
    selected_company = st.selectbox("Company:", list(companies.values()), index=None, placeholder="Select a company")

st.markdown("<hr>", unsafe_allow_html=True)

# ==========================
# LOAD DATA WHEN COMPANY SELECTED
# ==========================
if selected_company:
    ticker = [k for k, v in companies.items() if v == selected_company][0]

    if ticker not in st.session_state.finance_data:
        with st.spinner(f"Loading data for {selected_company}..."):
            # Téléchargement via tes fonctions
            df_raw = get_stock_data([ticker])
            df_pct = get_pct_change_df([ticker])

            # Si multi-index (plusieurs tickers)
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw = df_raw[ticker]

            df_raw = df_raw.reset_index()
            df_raw.columns = [c.lower() for c in df_raw.columns]

            # Ajout du % d’évolution
            if ticker in df_pct.columns:
                df_raw["price_change_pct"] = df_pct[ticker].values
            else:
                df_raw["price_change_pct"] = np.nan

            # Données fictives pour sentiment et nb_messages
            df_raw["sentiment"] = np.random.uniform(-1, 1, len(df_raw))
            df_raw["nb_messages"] = np.random.randint(100, 1000, len(df_raw))

            st.session_state.finance_data[ticker] = df_raw
    else:
        df_fin = st.session_state.finance_data[ticker]

    df_fin = st.session_state.finance_data[ticker]
else:
    df_fin = pd.DataFrame()

# ==========================
# KPI BOXES
# ==========================
kpi_cols = st.columns(5)

if not df_fin.empty:
    latest = df_fin.iloc[-1]
    metrics = {
        "Open": latest.get("open", None),
        "Close": latest.get("close", None),
        "High": latest.get("high", None),
        "Low": latest.get("low", None),
        "Sentiment": latest.get("sentiment", None)
    }
else:
    metrics = {label: None for label in ["Open", "Close", "High", "Low", "Sentiment"]}

for i, (label, value) in enumerate(metrics.items()):
    val_display = f"{value:.2f}" if value is not None and not pd.isna(value) else "--"
    with kpi_cols[i]:
        st.markdown(
            f"""
            <div style="
                background-color:{COLORS['inner']};
                padding:20px;
                border-radius:15px;
                border: 1px solid {COLORS['border']};
                text-align:center;
                height: 100px;
                display:flex;
                flex-direction:column;
                justify-content:center;
            ">
                <h2 style='color:{COLORS['accent']}; margin:0; font-size:34px; font-weight:800;'>{val_display}</h2>
                <p style='color:{COLORS['card']}; margin:0; font-size:14px;'>{label}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# GRAPH TOGGLE TITLE
# ==========================
col_graph_title = st.columns([9, 0.5])
with col_graph_title[0]:
    title_text = (
        "📈 Price % Change & Sentiment Score (30 days)"
        if st.session_state.view == 1
        else "📊 Trading Volume & Message Count (30 days)"
    )
    st.markdown(
        f"<h2 style='color:{COLORS['text']}; font-weight:700; margin-bottom:10px;'>{title_text}</h2>",
        unsafe_allow_html=True
    )
with col_graph_title[1]:
    if st.button("➡️", key="toggle_graph", help="Switch graph view", use_container_width=True):
        st.session_state.view = 2 if st.session_state.view == 1 else 1
        st.rerun()

# ==========================
# MAIN GRAPH
# ==========================
fig = go.Figure()

if not df_fin.empty:
    if st.session_state.view == 1:
        fig.add_trace(go.Scatter(
            x=df_fin["date"], y=df_fin["price_change_pct"],
            name="% Price Change",
            line=dict(color=COLORS["accent"], width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_fin["date"], y=df_fin["sentiment"],
            name="Sentiment Score",
            yaxis="y2",
            line=dict(color=COLORS["gray"], width=2, dash="dot")
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis=dict(title="% Price Change"),
            yaxis2=dict(title="Sentiment Score", overlaying="y", side="right"),
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=40, b=20)
        )
    else:
        fig.add_trace(go.Scatter(
            x=df_fin["date"], y=df_fin["volume"],
            name="Trading Volume",
            line=dict(color=COLORS["accent"], width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_fin["date"], y=df_fin["nb_messages"],
            name="Messages/Posts",
            yaxis="y2",
            line=dict(color=COLORS["lightgray"], width=2, dash="dot")
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis=dict(title="Trading Volume"),
            yaxis2=dict(title="Messages/Posts", overlaying="y", side="right"),
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=40, b=20)
        )
else:
    fig.update_layout(
        template="plotly_dark",
        annotations=[dict(text="No data available", x=0.5, y=0.5, showarrow=False, font=dict(size=20))],
        height=450
    )

st.plotly_chart(fig, use_container_width=True)

# ==========================
# PIE CHARTS
# ==========================
st.markdown("<br><br>", unsafe_allow_html=True)
col_pie1, col_pie2 = st.columns(2)

with col_pie1:
    if not df_fin.empty:
        sentiment_counts = {
            "Positive": np.sum(df_fin["sentiment"] > 0.2),
            "Neutral": np.sum((df_fin["sentiment"] <= 0.2) & (df_fin["sentiment"] >= -0.2)),
            "Negative": np.sum(df_fin["sentiment"] < -0.2)
        }
        fig_pie1 = px.pie(
            names=list(sentiment_counts.keys()),
            values=list(sentiment_counts.values()),
            title="Sentiment Distribution",
            color_discrete_sequence=[COLORS["accent"], COLORS["gray"], COLORS["inner"]],
            hole=0.4
        )
        fig_pie1.update_traces(marker_line_color=COLORS["border"], marker_line_width=0.6)
        fig_pie1.update_layout(template="plotly_dark")
        st.plotly_chart(fig_pie1, use_container_width=True)
    else:
        st.info("No sentiment data available.")

with col_pie2:
    sources = {"Twitter": np.random.randint(40, 60), "Reddit": np.random.randint(40, 60)}
    fig_pie2 = px.pie(
        names=list(sources.keys()),
        values=list(sources.values()),
        title="Source Distribution",
        color_discrete_sequence=[COLORS["accent"], COLORS["inner"]],
        hole=0.4
    )
    fig_pie2.update_traces(marker_line_color=COLORS["border"], marker_line_width=0.6)
    fig_pie2.update_layout(template="plotly_dark")
    st.plotly_chart(fig_pie2, use_container_width=True)

st.markdown(f"<div style='height:100px; background-color:{COLORS['bg']};'></div>", unsafe_allow_html=True)
