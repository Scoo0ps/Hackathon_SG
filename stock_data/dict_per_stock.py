import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta



def get_stock_data(
    tickers,
    days_back=30,
    include_today=True
):
    """
    Télécharge les données boursières pour une liste de tickers via yfinance.
    
    Args:
        tickers (str): Symbole boursier à télécharger.
        days_back (int): Nombre de jours à remonter dans le passé.
        include_today (bool): Si True, la période s’arrête à aujourd’hui.
    
    Returns:
        pd.DataFrame: Données boursières groupées par ticker.
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
    
    # Téléchargement via yfinance
    data = yf.download(
        tickers,
        start=start_date_str,
        end=end_date_str,
        group_by='ticker',
        auto_adjust=True
    )
    
    return data


# --- TEST DE LA FONCTION ---
if __name__ == "__main__":
    data = get_stock_data(tickers="AAPL", days_back=10)  # ⬅️ Appel de la fonction

    # --- AFFICHAGE DU DATAFRAME AAPL ---
    if "AAPL" in data:
        print("\n=== 🧾 DataFrame complet pour AAPL ===")
        print(data["AAPL"])
    else:
        print("\n⚠️ AAPL n'est pas présent dans les données téléchargées.")