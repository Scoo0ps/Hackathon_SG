import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_pct_change_df(
    tickers,
    days_back=30,
    include_today=True
):
    """
    Télécharge les données boursières pour un ticker via yfinance,
    calcule le % d'évolution journalière ((Close - Open) / Open) * 100,
    et retourne un DataFrame avec ces données pour chaque ticker.

    Args:
        tickers (str): Symbole boursier à télécharger.
        days_back (int): Nombre de jours à remonter dans le passé.
        include_today (bool): Si True, la période s’arrête à aujourd’hui.

    Returns:
        pd.DataFrame: DataFrame avec les dates en index et le ticker en colonnes.
    """
    # Gestion dynamique des dates
    end_date = datetime.now()
    if not include_today:
        end_date -= timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"\n📅 Période : {start_date_str} → {end_date_str}")
    print(f"📈 Tickers : {tickers}\n")

    # Téléchargement groupé
    data = yf.download(
        tickers,
        start=start_date_str,
        end=end_date_str,
        group_by='ticker',
        auto_adjust=True
    )

    pct_changes = {}
    if tickers in data:
        df = data[tickers]
        pct_change = ((df["Close"] - df["Open"]) / df["Open"]) * 100
        pct_changes[tickers] = pct_change
    else:
        print(f"⚠️ Pas de données pour {tickers}")

    df_pct_change = pd.DataFrame(pct_changes).sort_index()
    return df_pct_change

# --- TEST DE LA FONCTION ---
if __name__ == "__main__":
    df_pct = get_pct_change_df("AAPL", days_back=5)  # ⬅️ Appel de la fonction
    print("\n=== 🧾 DataFrame des % d'évolution journalière ===")
    print(df_pct.head())