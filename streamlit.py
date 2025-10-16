import streamlit as st
from stock_data.dict_per_stock import get_stock_data
from stock_data.dataframe_percent import get_pct_change_df

# Récupération des données
data = get_stock_data()
df_pct = get_pct_change_df()

# Sélection du ticker
tickers = list(data.keys())
selected_ticker = st.selectbox("Sélectionnez une action", tickers)

# Affichage des valeurs brutes
st.write(f"**Données brutes pour {selected_ticker}**")
st.dataframe(data[selected_ticker])

# Affichage du graphe d'évolution
st.write(f"**Évolution journalière (%) pour {selected_ticker}**")
st.line_chart(df_pct[selected_ticker])