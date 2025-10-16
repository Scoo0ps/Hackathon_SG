import yfinance as yf

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


for t in tickers:
    prices = yf.download(t, period="7d", interval="1d")
    print(prices)