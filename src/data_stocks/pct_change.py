import yfinance as yf
import pandas as pd
import os

# Crée le dossier de sortie
os.makedirs("data", exist_ok=True)

tickers = [
    "AIR.PA", "BNP.PA", "SAN.PA", "MC.PA", "OR.PA",
    "DG.PA", "SU.PA", "ENGI.PA", "CAP.PA", "KER.PA",
    "AAPL", "MSFT", "GOOG", "AMZN", "META",
    "NVDA", "TSLA", "PEP", "AVGO", "ADBE"
]

all_pct_change = []

for t in tickers:
    print(f"⬇️ Téléchargement de {t} ...")
    df = yf.download(t, period="30d", interval="1d", group_by='ticker', auto_adjust=False)

    if df.empty:
        print(f"⚠️ Pas de données pour {t}")
        continue

    # Si MultiIndex sur les colonnes, on cherche les colonnes Open et Close sans aplatir
    if isinstance(df.columns, pd.MultiIndex):
        # Par exemple: ('Price', 'Open'), ('Price', 'Close')
        open_col = None
        close_col = None

        # Recherche dans le MultiIndex
        for col in df.columns:
            if 'Open' in col:
                open_col = col
            elif 'Close' in col:
                close_col = col

        if open_col is None or close_col is None:
            print(f"⚠️ Colonnes Open/Close manquantes pour {t} dans MultiIndex")
            continue

        # Calcul variation %
        df['Pct_change'] = ((df[close_col] - df[open_col]) / df[open_col]) * 100

    else:
        # Si colonnes simples
        if 'Open' not in df.columns or 'Close' not in df.columns:
            print(f"⚠️ Colonnes Open/Close manquantes pour {t} dans colonnes simples")
            continue

        df['Pct_change'] = ((df['Close'] - df['Open']) / df['Open']) * 100

    # Extraire la colonne Pct_change et renommer avec le ticker
    tmp = df[['Pct_change']].copy()
    tmp.rename(columns={'Pct_change': t}, inplace=True)

    all_pct_change.append(tmp)

# Fusion sur l'index (les dates)
if not all_pct_change:
    raise ValueError("❌ Aucun ticker valide.")

result_df = pd.concat(all_pct_change, axis=1).sort_index()

# Export CSV
output_path = "../../data/pct_change_table.csv"
result_df.to_csv(output_path)

print(f"✅ Export terminé : {output_path}")
print(result_df.head())
