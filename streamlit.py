import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from stock_data.dict_per_stock import get_stock_data
from stock_data.dataframe_percent import get_pct_change_df

# --- Chargement des données ---
data = get_stock_data()
df_pct = get_pct_change_df()

# --- Détection des tickers ---
if isinstance(data.columns, pd.MultiIndex):
    # suppose que le MultiIndex est du type ('AAPL', 'Open')
    tickers = sorted(set(data.columns.get_level_values(0)))
else:
    tickers = sorted(data.columns)

selected_ticker = st.selectbox("Sélectionnez une action", tickers)

st.header(f"Données pour {selected_ticker}")

# --- Sélection de la série pour le ticker choisi ---
# Cas MultiIndex (data['AAPL']['Open'] ou df_pct['AAPL'])
if isinstance(df_pct.columns, pd.MultiIndex):
    # prend la première colonne du ticker si plusieurs (ex: 'Close' ou '%Change')
    first_col = df_pct[selected_ticker].columns[0] if hasattr(df_pct[selected_ticker], "columns") else None
    y_data = df_pct[selected_ticker][first_col] if first_col else df_pct[selected_ticker]
else:
    y_data = df_pct[selected_ticker]

# --- Graphique ---
st.subheader("Évolution journalière (%) sur 30 jours")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(y_data.index, y_data.values, marker='o', linestyle='-', color='royalblue')
ax.set_title(f"Évolution journalière (%) - {selected_ticker}")
ax.set_xlabel("Date")
ax.set_ylabel("Variation (%)")
plt.xticks(rotation=45)

st.pyplot(fig)

# --- Option : afficher les dernières valeurs ---
st.subheader("Dernières variations")
st.dataframe(y_data.tail(10))
