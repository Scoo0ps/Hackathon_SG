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
