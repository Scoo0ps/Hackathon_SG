import pandas as pd
import os


clean_folder = "../../data/per_stock_clean"

dfs = {}

for filename in os.listdir(clean_folder):
    if filename.endswith(".csv"):
        ticker = filename.replace(".csv", "")
        file_path = os.path.join(clean_folder, filename)
        
        df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
        dfs[ticker] = df

print("\nTickers chargés :", list(dfs.keys()))


# Aperçu d’un DataFrame (AAPL)
print("\n--- Aperçu de AAPL ---")
print(dfs["AAPL"].head())


# Calcul du % d'évolution journalière pour chaque action
pct_changes = {}

for ticker, df in dfs.items():
    # ((Close - Open) / Open) * 100
    pct_change = ((df["Close"] - df["Open"]) / df["Open"]) * 100
    pct_changes[ticker] = pct_change

# Construction du DataFrame final
df_pct_change = pd.DataFrame(pct_changes).sort_index()

# Export CSV dans ../../data/
output_path = "../../data/daily_pct_change.csv"
df_pct_change.to_csv(output_path, index=True, date_format="%Y-%m-%d")

print(f"\n✅ Fichier daily_pct_change.csv créé dans : {output_path}")
print("\nAperçu du fichier :")
print(df_pct_change.head())

