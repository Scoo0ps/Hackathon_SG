import yfinance as yf
import pandas as pd


# Société Générale (GLE.PA), Tesla (TSLA), Bitcoin (BTC-USD)
tickers = [
    # CAC 40 (France)
    "AIR.PA",  # Airbus
    "BNP.PA",  # BNP Paribas
    "SAN.PA",  # Sanofi
    "MC.PA",   # LVMH
    "OR.PA",   # L'Oréal
    "DG.PA",   # Vinci
    "SU.PA",   # Schneider Electric
    "ENGI.PA", # Engie
    "CAP.PA",  # Capgemini
    "KER.PA",  # Kering

    # NASDAQ 100 (USA)
    "AAPL",    # Apple
    "MSFT",    # Microsoft
    "GOOG",    # Alphabet (Google)
    "AMZN",    # Amazon
    "META",    # Meta Platforms
    "NVDA",    # Nvidia
    "TSLA",    # Tesla
    "PEP",     # PepsiCo
    "AVGO",    # Broadcom
    "ADBE"     # Adobe
]


dfs = []

for t in tickers:
    df = yf.download(t, period="7d", interval="1d")
    if df.empty:
        continue
    # Calcul variation en %
    df["Pct_change"] = ((df["Close"] - df["Open"]) / df["Open"]) * 100
    # Ajout d’une colonne ticker pour identifier les données
    df["Ticker"] = t
    # Sélection colonnes
    df = df[["Ticker", "Open", "High", "Low", "Close", "Pct_change", "Volume"]]
    # Reset index pour avoir la date en colonne
    df = df.reset_index()
    dfs.append(df)

# Concaténer tous les DataFrames en un seul
final_df = pd.concat(dfs, ignore_index=True)

print(final_df.head(15))
