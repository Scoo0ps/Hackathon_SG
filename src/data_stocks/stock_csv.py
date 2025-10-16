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

from datetime import datetime, timedelta

# Date d'hier
end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# Date 30 jours avant hier
start_date = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')

print("start_date =", start_date)
print("end_date =", end_date)


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
