import yfinance as yf
import pandas as pd

ticker = "AIR.PA"
date = "2025-10-08"

# Télécharger données, index en datetime
df = yf.download(ticker, start=date, end="2025-10-09", interval="1d", auto_adjust=False)

# Convertir l'index en string format YYYY-MM-DD
df.index = df.index.strftime('%Y-%m-%d')

# Extraire la ligne correspondant à la date ciblée
if date in df.index:
    row = df.loc[date]
    open_price = row['Open']
    close_price = row['Close']
    pct_change = ((close_price - open_price) / open_price) * 100
    print(f"Variation {ticker} le {date} : {pct_change:.6f}%")
else:
    print("Données introuvables pour la date spécifiée.")
