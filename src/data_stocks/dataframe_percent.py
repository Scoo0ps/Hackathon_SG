import pandas as pd
import os

def load_pct_change_data(clean_folder="../../data/per_stock_clean"):
    """
    Charge les fichiers CSV des actions dans le dossier donné,
    calcule le % d'évolution journalière ((Close - Open) / Open) * 100,
    et retourne un DataFrame avec ces données pour chaque ticker.

    Args:
        clean_folder (str): chemin vers le dossier contenant les fichiers CSV.

    Returns:
        pd.DataFrame: DataFrame avec les dates en index et les tickers en colonnes.
    """
    dfs = {}

    for filename in os.listdir(clean_folder):
        if filename.endswith(".csv"):
            ticker = filename.replace(".csv", "")
            file_path = os.path.join(clean_folder, filename)
            
            df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
            dfs[ticker] = df

    pct_changes = {}

    for ticker, df in dfs.items():
        pct_change = ((df["Close"] - df["Open"]) / df["Open"]) * 100
        pct_changes[ticker] = pct_change

    df_pct_change = pd.DataFrame(pct_changes).sort_index()

    return df_pct_change

# Exemple d'utilisation
if __name__ == "__main__":
    df_pct = load_pct_change_data()
    print(df_pct.head())
