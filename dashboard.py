import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

from stock_data.dict_per_stock import get_stock_data
from stock_data.dataframe_percent import get_pct_change_df
from sentiment_analysis_textblob import main_analyse_textblob
from sentiment_analysis_finbert import main_analyse_finbert

from correlation import score_compatibilite_df

# ==========================
# CONFIG
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

GRAPH_BG = "#F5F5F5"
GRAPH_HEIGHT = 360

# ==========================
# SESSION STATE INIT
# ==========================
if "view" not in st.session_state:
    st.session_state.view = 1
if "finance_data" not in st.session_state:
    st.session_state.finance_data = {}
if "sentiment_data" not in st.session_state:
    st.session_state.sentiment_data = {}
if "selected_company" not in st.session_state:
    st.session_state.selected_company = "Apple Inc."
if "mode" not in st.session_state:
    st.session_state.mode = "⚡ Fast & less accurate"
if "selected_date" not in st.session_state:
    st.session_state.selected_date = (datetime.now() - timedelta(days=1)).date()
if "previous_mode" not in st.session_state:
    st.session_state.previous_mode = "⚡ Fast & less accurate"

# ==========================
# CSS
# ==========================
st.markdown(
    f"""
    <style>
    .block-container {{
        padding: 1rem 2rem;
        background-color:{COLORS['bg']};
        color:{COLORS['text']};
    }}
    h1, h2, h3, h4, h5, h6, p, label {{
        color:{COLORS['text']};
    }}
    .stSelectbox > div, .stRadio > div, .stDateInput > div {{
        background-color:{COLORS['card']};
        color:{COLORS['text']};
        border-radius: 10px;
        padding: 6px 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================
# STOCKS LIST
# ==========================
STOCK_KEYWORDS = {
    # French CAC 40 Stocks
    "AIR.PA": {"company": "Airbus SE"},
    "MC.PA": {"company": "LVMH Moët Hennessy Louis Vuitton SE"},
    # US Tech & Blue Chip
    "AAPL": {"company": "Apple Inc."},
    "MSFT": {"company": "Microsoft Corporation"},
    "GOOG": {"company": "Alphabet Inc. (Google)"},
    "AMZN": {"company": "Amazon.com Inc."},
    "META": {"company": "Meta Platforms Inc."},
    "NVDA": {"company": "NVIDIA Corporation"},
    "TSLA": {"company": "Tesla Inc."},
    "PEP": {"company": "PepsiCo Inc."},
}

companies = {ticker: info["company"] for ticker, info in STOCK_KEYWORDS.items()}

# ==========================
# HEADER
# ==========================
st.markdown(
    f"<h1 style='color:{COLORS['accent']}; text-align:center; font-size:54px; font-weight:900; margin-bottom:30px; margin-top:20px;'>SG Market & Sentiment Dashboard</h1>",
    unsafe_allow_html=True
)

# ==========================
# FILTERS LINE
# ==========================
col_mode, col_company, col_date = st.columns([2, 3, 2])

with col_mode:
    mode_selected = st.radio(
        "Mode selection:",
        ["⚡ Fast & less accurate", "⏳ Slow & more accurate"],
        horizontal=True,
        index=0 if st.session_state.mode=="⚡ Fast & less accurate" else 1,
        key="mode_radio"
    )
    
    # Détecter le changement de mode et réinitialiser les données sentiment
    if mode_selected != st.session_state.previous_mode:
        st.session_state.sentiment_data = {}
        st.session_state.previous_mode = mode_selected
        st.session_state.mode = mode_selected
    else:
        st.session_state.mode = mode_selected

with col_company:
    st.session_state.selected_company = st.selectbox(
        "Company:",
        list(companies.values()),
        index=list(companies.values()).index(st.session_state.selected_company),
        key="company_select"
    )

with col_date:
    min_date = datetime.now().date() - timedelta(days=30)
    max_date = datetime.now().date() - timedelta(days=1)
    st.session_state.selected_date = st.date_input(
        "Select Date:",
        value=st.session_state.selected_date,
        min_value=min_date,
        max_value=max_date,
        key="date_select"
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ==========================
# LOAD DATA
# ==========================
ticker = [k for k, v in companies.items() if v == st.session_state.selected_company][0]

# Load Financial Data
if ticker not in st.session_state.finance_data:
    with st.spinner(f"Loading financial data for {st.session_state.selected_company}..."):
        df_raw = get_stock_data(tickers=ticker, days_back=30, include_today=True)
        df_pct = get_pct_change_df(tickers=ticker, days_back=30, include_today=True)

        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw = df_raw[ticker]

        df_raw = df_raw.reset_index()
        df_raw.columns = [c.lower() for c in df_raw.columns]

        if ticker in df_pct.columns:
            df_raw["price_change_pct"] = df_pct[ticker].values
        else:
            df_raw["price_change_pct"] = np.nan

        df_raw["nb_messages"] = np.random.randint(50, 1000, size=len(df_raw))

        st.session_state.finance_data[ticker] = df_raw

df_fin = st.session_state.finance_data[ticker]

# ==========================
# LOAD SENTIMENT DATA
# ==========================
if ticker not in st.session_state.sentiment_data:
    with st.spinner(f"Loading sentiment data for {st.session_state.selected_company}..."):
        try:
            # Choix du mode d'analyse
            if st.session_state.mode == "⏳ Slow & more accurate":
                df_sentiment = main_analyse_finbert(ticker)
            else:
                df_sentiment = main_analyse_textblob(ticker)

            # Vérifier si on a des résultats
            if df_sentiment is not None and not df_sentiment.empty:
                df_sentiment['analysis_date'] = pd.to_datetime(df_sentiment['analysis_date']).dt.date
                st.session_state.sentiment_data[ticker] = df_sentiment
            else:
                # DataFrame vide si pas de messages
                st.session_state.sentiment_data[ticker] = pd.DataFrame()

        except Exception as e:
            st.warning(f"Erreur lors du chargement du sentiment: {e}")
            st.session_state.sentiment_data[ticker] = pd.DataFrame()

df_sentiment = st.session_state.sentiment_data[ticker]

# Fusionner avec les données financières
df_fin['date_only'] = df_fin['date'].dt.date

if not df_sentiment.empty:
    df_fin = df_fin.merge(
        df_sentiment[['analysis_date', 'GlobalScore', 'MessageCount']], 
        left_on='date_only', right_on='analysis_date', how='left'
    )
    # Si pas de données pour certains jours, mettre NaN au lieu d'inventer
    df_fin['sentiment'] = df_fin['GlobalScore']
    df_fin['nb_messages'] = df_fin['MessageCount']
    df_fin = df_fin.drop(['date_only', 'analysis_date', 'GlobalScore', 'MessageCount'], axis=1)
else:
    df_fin['sentiment'] = np.nan
    df_fin = df_fin.drop(['date_only'], axis=1)

# ==========================
# KPI BOXES
# ==========================
kpi_cols = st.columns(6)

selected_row = df_fin[df_fin["date"].dt.date == st.session_state.selected_date]
if selected_row.empty:
    selected_row = df_fin.iloc[[-1]]

latest = selected_row.iloc[0]

metrics = {
    "Open": latest.get("open", None),
    "Close": latest.get("close", None),
    "High": latest.get("high", None),
    "Low": latest.get("low", None),
    "Volume": latest.get("volume", None),
    "Sentiment": latest.get("sentiment", None)
}

for i, (label, value) in enumerate(metrics.items()):
    if label == "Volume" and value is not None and not pd.isna(value):
        val_display = f"{int(value):,}".replace(",", " ")
    elif label != "Volume" and value is not None and not pd.isna(value):
        val_display = f"{value:.2f}"
    else:
        val_display = "--"
    with kpi_cols[i]:
        st.markdown(
            f"""
            <div style="
                background-color:{GRAPH_BG};
                padding:20px;
                border-radius:15px;
                border: 1px solid {COLORS['border']};
                text-align:center;
                height: 100px;
                display:flex;
                flex-direction:column;
                justify-content:center;
            ">
                <h2 style='color:{COLORS['accent']}; margin:0; font-size:28px; font-weight:800;'>{val_display}</h2>
                <p style='color:#333333; margin:0; font-size:14px;'>{label}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# Graphique principal + flèche
# ==========================
col_graph_title = st.columns([9,0.5])

with col_graph_title[0]:
    title_text = "📈 Price % Change & Sentiment Score (30 days)" if st.session_state.view==1 else "📊 Trading Volume & Message Count (30 days)"
    st.markdown(f"<h2 style='color:{COLORS['text']}; font-weight:700; margin-bottom:10px;'>{title_text}</h2>", unsafe_allow_html=True)

with col_graph_title[1]:
    if st.button("➡️", key="toggle_graph", help="Switch graph view"):
        st.session_state.view = 2 if st.session_state.view==1 else 1
        st.rerun()

fig_main = go.Figure()
if st.session_state.view==1:
    fig_main.add_trace(go.Scatter(x=df_fin["date"], y=df_fin["price_change_pct"], name="% Price Change", line=dict(color=COLORS["accent"], width=3)))
    fig_main.add_trace(go.Scatter(x=df_fin["date"], y=df_fin["sentiment"], name="Sentiment Score", yaxis="y2", line=dict(color=COLORS["gray"], width=2, dash="dot")))
    fig_main.update_layout(
        xaxis_title="Date",
        yaxis=dict(title="% Price Change"),
        yaxis2=dict(title="Sentiment Score", overlaying="y", side="right"),
        template="plotly_dark",
        height=450,
        margin=dict(l=10,r=10,t=40,b=20),
        plot_bgcolor=GRAPH_BG,
        paper_bgcolor=GRAPH_BG
    )
else:
    fig_main.add_trace(go.Scatter(x=df_fin["date"], y=df_fin["volume"], name="Trading Volume", line=dict(color=COLORS["accent"], width=3)))
    fig_main.add_trace(go.Scatter(x=df_fin["date"], y=df_fin["nb_messages"], name="Messages/Posts", yaxis="y2", line=dict(color=COLORS["lightgray"], width=2, dash="dot")))
    fig_main.update_layout(
        xaxis_title="Date",
        yaxis=dict(title="Trading Volume"),
        yaxis2=dict(title="Messages/Posts", overlaying="y", side="right"),
        template="plotly_dark",
        height=450,
        margin=dict(l=10,r=10,t=40,b=20),
        plot_bgcolor=GRAPH_BG,
        paper_bgcolor=GRAPH_BG
    )

# Afficher avec bouton de zoom activé
st.plotly_chart(fig_main, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# ==========================
# Pie charts + jauge
# ==========================
st.markdown("<br><br>", unsafe_allow_html=True)

chart_title_font = dict(size=18, color="#FFFFFF", family="Arial", weight='bold')
chart_font = dict(size=12, color="#FFFFFF", family="Arial")

if st.session_state.mode == "⏳ Slow & more accurate":
    # Mode avec 3 graphiques
    col_pie1, col_gauge, col_pie2 = st.columns([2,1,2])
    
    # Pie sentiment
    with col_pie1:
        st.markdown(f"<h3 style='color:{COLORS['text']}; text-align:center; margin-bottom:10px;'>Sentiment Distribution</h3>", unsafe_allow_html=True)
        
        # Utiliser les colonnes Positive, Neutral, Negative du DataFrame sentiment
        if not df_sentiment.empty and all(col in df_sentiment.columns for col in ['Positive', 'Neutral', 'Negative']):
            # Calculer la somme totale des scores sur tout le mois
            total_positive = df_sentiment["Positive"].sum()
            total_neutral = df_sentiment["Neutral"].sum()
            total_negative = df_sentiment["Negative"].sum()
            
            sentiment_counts = {
                "Positive": total_positive,
                "Neutral": total_neutral,
                "Negative": total_negative
            }
        else:
            # Fallback si les données ne sont pas disponibles
            sentiment_counts = {
                "Positive": 0,
                "Neutral": 0,
                "Negative": 0
            }
        
        fig_pie_sentiment = px.pie(
            names=list(sentiment_counts.keys()),
            values=list(sentiment_counts.values()),
            hole=0.4,
            color_discrete_sequence=[COLORS["gray"], "#FFFFFF", COLORS["accent"]]  # Gris, Blanc, Rouge
        )
        fig_pie_sentiment.update_layout(
            paper_bgcolor=COLORS['bg'],
            plot_bgcolor=COLORS['bg'],
            font=dict(size=12, color="#FFFFFF", family="Arial"),
            height=GRAPH_HEIGHT,
            showlegend=True,
            legend=dict(font=dict(color="#FFFFFF")),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_pie_sentiment, use_container_width=True, config={"displayModeBar": False})
else:
    # Mode avec 2 graphiques (plus larges)
    col_gauge, col_pie2 = st.columns([1,1])

# ==========================
# JAUGE - Performance Score
# ==========================
with col_gauge:
    st.markdown(f"<h3 style='color:{COLORS['text']}; text-align:center; margin-bottom:10px;'>Performance Score</h3>", unsafe_allow_html=True)
    try:
        if not df_sentiment.empty:
            y2_dict = {
                "GlobalScore": df_sentiment["GlobalScore"].tolist(),
                "analysis_date": df_sentiment["analysis_date"].astype(str).tolist()
            }
            y1 = get_pct_change_df(ticker)
            min_date = pd.to_datetime(min(y2_dict["analysis_date"]))
            max_date = pd.to_datetime(max(y2_dict["analysis_date"]))
            y1 = y1.loc[min_date:max_date]

            gauge_value = score_compatibilite_df(y1, y2_dict)
        else:
            gauge_value = np.nan
    except Exception as e:
        st.warning(f"Erreur lors du calcul du score de compatibilité : {e}")
        gauge_value = np.nan

    if np.isnan(gauge_value):
        gauge_value = 0
    
    gauge_color = COLORS["accent"]  # Toujours rouge

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_value,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': gauge_color},
            'bgcolor': COLORS['bg']
        },
        number={'suffix': '%', 'font': {'color': COLORS['text'], 'size': 24}}
    ))
    fig_gauge.update_layout(
        height=GRAPH_HEIGHT,
        paper_bgcolor=COLORS['bg'],
        font=chart_font,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

# Pie sources
with col_pie2:
    st.markdown(f"<h3 style='color:{COLORS['text']}; text-align:center; margin-bottom:10px;'>Source Distribution</h3>", unsafe_allow_html=True)
    sources = {"Twitter": np.random.randint(40,60), "Reddit": np.random.randint(40,60)}
    fig_pie_sources = px.pie(
        names=list(sources.keys()),
        values=list(sources.values()),
        hole=0.4,
        color_discrete_sequence=[COLORS["accent"], COLORS["inner"]]
    )
    fig_pie_sources.update_layout(
        paper_bgcolor=COLORS['bg'],
        plot_bgcolor=COLORS['bg'],
        font=dict(size=12, color="#FFFFFF", family="Arial"),
        height=GRAPH_HEIGHT,
        showlegend=True,
        legend=dict(font=dict(color="#FFFFFF")),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_pie_sources, use_container_width=True, config={"displayModeBar": False})

st.markdown(f"<div style='height:100px; background-color:{COLORS['bg']};'></div>", unsafe_allow_html=True)