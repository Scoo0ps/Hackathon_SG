import yfinance as yf
import pandas as pd
import os

# Crée le dossier de sortie
os.makedirs("data", exist_ok=True)

# Liste des tickers
tickers = [
    "AIR.PA", "BNP.PA", "SAN.PA", "MC.PA",
    "DG.PA", "SU.PA", "ENGI.PA", "KER.PA",
    "AAPL", "MSFT", "GOOG", "AMZN", "META",
    "NVDA", "TSLA", "PEP"
]

# Période demandée
start_date = "2025-09-15"
end_date = "2025-10-15"

for ticker in tickers:
    print(f"Téléchargement de {ticker}...")
    data = yf.download(ticker, start=start_date, end=end_date)

    if not data.empty:
        # Sauvegarde en CSV avec la date comme index
        file_path = os.path.join("../../data/per_stock", f"{ticker}.csv")
        data.to_csv(file_path, index=True, date_format="%Y-%m-%d")
        print(f"✅ Enregistré : {file_path}")
    else:
        print(f"⚠️ Aucune donnée trouvée pour {ticker}")

print("\nTéléchargement terminé !")
