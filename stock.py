import yfinance as yf
import pandas as pd
import os

# Dossier de sortie
os.makedirs("data", exist_ok=True)

tickers = [
    "AIR.PA",  # Airbus SE
    "BNP.PA",  # BNP Paribas SA
    "SAN.PA",  # Sanofi SA
    "MC.PA",   # LVMH Moët Hennessy Louis Vuitton SE
    "OR.PA",   # L'Oréal SA
    "DG.PA",   # Vinci SA
    "SU.PA",   # Schneider Electric SE
    "ENGI.PA", # Engie SA
    "CAP.PA",  # Capgemini SE
    "KER.PA",  # Kering SA
    "AAPL",    # Apple Inc.
    "MSFT",    # Microsoft Corporation
    "GOOG",    # Alphabet Inc. (Google)
    "AMZN",    # Amazon.com Inc.
    "META",    # Meta Platforms Inc. (Facebook)
    "NVDA",    # NVIDIA Corporation
    "TSLA",    # Tesla Inc.
    "PEP",     # PepsiCo Inc.
    "AVGO",    # Broadcom Inc.
    "ADBE"     # Adobe Inc.
]

all_data = []

for t in tickers:
    print(f"⬇️ Téléchargement de {t} ...")
    df = yf.download(t, period="7d", interval="1d", group_by='ticker', auto_adjust=False)
    
    if df.empty:
        print(f"⚠️ Aucune donnée pour {t}")
        continue

    # --- 🔹 Si colonnes multi-index, on les aplati proprement
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]

    # --- 🔹 Recherche intelligente des colonnes Open / Close
    open_col = [c for c in df.columns if "Open" in c]
    close_col = [c for c in df.columns if "Close" in c]

    if not open_col or not close_col:
        print(f"⚠️ Colonnes Open/Close introuvables pour {t}, ignoré.")
        print(f"Colonnes disponibles : {list(df.columns)}")
        continue

    # On prend le premier match trouvé (car il y aura "AAPL_Open", "AAPL_Close", etc.)
    open_col = open_col[0]
    close_col = close_col[0]

    # --- 🔹 Calcul du pourcentage de variation
    df["Pct_change"] = ((df[close_col] - df[open_col]) / df[open_col]) * 100

    # --- 🔹 Ajout du ticker et de la date
    df["Ticker"] = t
    df["Date"] = df.index

    all_data.append(df[["Date", "Ticker", "Pct_change"]])

# --- 🔹 Fusion finale
if not all_data:
    raise ValueError("❌ Aucun ticker n’a produit de données valides.")

full_df = pd.concat(all_data, ignore_index=True)

# --- 🔹 Pivot (dates en lignes, tickers en colonnes)
pivot_df = full_df.pivot(index="Date", columns="Ticker", values="Pct_change").sort_index()

# --- 🔹 Export CSV
output_path = "data/pct_change_table.csv"
pivot_df.to_csv(output_path)

print(f"✅ Fichier exporté : {output_path}")
print(pivot_df.head())
