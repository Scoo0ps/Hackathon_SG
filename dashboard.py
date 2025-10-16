import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ==========================
# 🎨 CONFIG
# ==========================
st.set_page_config(page_title="SG Market & Sentiment Dashboard", layout="wide")

COLORS = {
    "bg": "#121212",           # background noir
    "card": "#2A2A2A",         # cartes gris foncé
    "inner": "#D9D9D9",        # intérieur gris très clair
    "text": "#FFFFFF",         # texte blanc
    "accent": "#D90429",       # rouge SG
    "gray": "#8D99AE",
    "border": "#000000",
    "lightgray": "#BDBDBD"
}

# ==========================
# CSS Global
# ==========================
st.markdown(
    f"""
    <style>
    .block-container {{
        padding: 1rem 2rem 1rem 2rem;
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
    /* Flèche noire sans contour blanc */
    button[kind="secondary"] {{
        background-color: {COLORS['bg']} !important;
        color: {COLORS['text']} !important;
        border: none !important;
        border-radius: 50%;
        width: 38px !important;
        height: 38px !important;
        font-size: 18px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================
# COMPANY NAMES
# ==========================
companies = {
    "AIR.PA": "Airbus SE",
    "BNP.PA": "BNP Paribas SA",
    "SAN.PA": "Sanofi SA",
    "MC.PA": "LVMH Moët Hennessy Louis Vuitton SE",
    "OR.PA": "L'Oréal SA",
    "DG.PA": "Vinci SA",
    "SU.PA": "Schneider Electric SE",
    "ENGI.PA": "Engie SA",
    "CAP.PA": "Capgemini SE",
    "KER.PA": "Kering SA",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOG": "Alphabet Inc. (Google)",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla Inc.",
    "PEP": "PepsiCo Inc.",
    "AVGO": "Broadcom Inc.",
    "ADBE": "Adobe Inc."
}

# ==========================
# FAKE DATA
# ==========================
days = 30
dates = pd.date_range(end=datetime.today(), periods=days)
np.random.seed(42)
df = pd.DataFrame({
    "date": dates,
    "open": np.random.uniform(150, 200, days),
    "close": np.random.uniform(150, 200, days),
    "high": np.random.uniform(200, 220, days),
    "low": np.random.uniform(140, 160, days),
    "volume": np.random.randint(1_000_000, 5_000_000, days),
    "price_change_pct": np.random.uniform(-5, 5, days),
    "sentiment": np.random.uniform(-1, 1, days),
    "nb_messages": np.random.randint(100, 1000, days)
})

# ==========================
# HEADER
# ==========================
st.markdown(
    f"""
    <div style='margin-top:20px;'>
        <h1 style='color:{COLORS['accent']}; text-align:center; font-size:54px; font-weight:900; margin-bottom:20px;'>
            SG Market & Sentiment Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Barre de sélection : Mode (gauche) / Entreprise (droite)
col_mode, _, col_select = st.columns([3, 5, 3])
with col_mode:
    mode = st.radio(
        "Mode selection:",
        ["⚡ Fast & less accurate", "⏳ Slow & more accurate"],
        horizontal=True,
        index=0
    )
with col_select:
    selected_company = st.selectbox("Company:", list(companies.values()), index=10, key="company")

st.markdown("<hr>", unsafe_allow_html=True)

# ==========================
# KPI BOXES
# ==========================
latest = df.iloc[-1]
kpi_cols = st.columns(5)
metrics = {
    "Open": latest["open"],
    "Close": latest["close"],
    "High": latest["high"],
    "Low": latest["low"],
    "Sentiment": latest["sentiment"]
}

for i, (label, value) in enumerate(metrics.items()):
    with kpi_cols[i]:
        st.markdown(
            f"""
            <div style="
                background-color:{COLORS['inner']};
                padding:25px;
                border-radius:15px;
                border: 1px solid {COLORS['border']};
                text-align:center;
                height: 120px;
                display:flex;
                flex-direction:column;
                justify-content:center;
            ">
                <h2 style='color:{COLORS['accent']}; margin:0; font-size:38px; font-weight:800;'>{value:.2f}</h2>
                <p style='color:{COLORS['card']}; margin:0; font-size:16px;'>{label}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# MAIN GRAPH
# ==========================
if "view" not in st.session_state:
    st.session_state.view = 1

title_text = (
    "📈 Price % Change & Sentiment Score (30 days)"
    if st.session_state.view == 1
    else "📊 Trading Volume & Message Count (30 days)"
)

# Titre + flèche noire à droite
col_graph_title = st.columns([9, 0.5])
with col_graph_title[0]:
    st.markdown(
        f"<h2 style='color:{COLORS['text']}; font-weight:700; margin-bottom:10px;'>{title_text}</h2>",
        unsafe_allow_html=True
    )
with col_graph_title[1]:
    if st.button("➡️", key="toggle_graph", help="Switch graph view", use_container_width=True):
        st.session_state.view = 2 if st.session_state.view == 1 else 1

fig = go.Figure()
if st.session_state.view == 1:
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["price_change_pct"],
        name="% Price Change",
        line=dict(color=COLORS["accent"], width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["sentiment"],
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
    # Deux courbes en ligne avec échelles séparées
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["volume"],
        name="Trading Volume",
        line=dict(color=COLORS["accent"], width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["nb_messages"],
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



st.plotly_chart(fig, use_container_width=True)

# ==========================
# PIE CHARTS
# ==========================
st.markdown("<br><br>", unsafe_allow_html=True)
col_pie1, col_pie2 = st.columns(2)

with col_pie1:
    sentiment_counts = {
        "Positive": np.sum(df["sentiment"] > 0.2),
        "Neutral": np.sum((df["sentiment"] <= 0.2) & (df["sentiment"] >= -0.2)),
        "Negative": np.sum(df["sentiment"] < -0.2)
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

# ==========================
# FOOTER
# ==========================
st.markdown(f"<div style='height:100px; background-color:{COLORS['bg']};'></div>", unsafe_allow_html=True)
