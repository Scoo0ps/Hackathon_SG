import numpy as np
import pandas as pd

from stock_data.dataframe_percent import get_pct_change_df  # Ton module perso
from sentiment_analysis_textblob import analyze_single_stock_textblob, analyze_single_stock_textblob, main_analyse_textblob   # Ton module perso


def score_compatibilite_df(y1: pd.DataFrame, y2: dict, col_name: str = None, max_lag_days: int = 7):
    """
    Calcule deux scores de compatibilité (0–100) entre un DataFrame y1 indexé par date
    et un dict y2 contenant 'GlobalScore' et 'analysis_date'.
    
    Limite la recherche des décalages (lags) à ±max_lag_days.
    
    Renvoie un dict avec les deux scores et leurs lags.
    """
    if col_name is None:
        col_name = y1.columns[0]

    dates = pd.to_datetime(y2["analysis_date"])
    values = np.array(y2["GlobalScore"]) * 100
    
    y2_df = pd.DataFrame(data={col_name: values}, index=dates)

    colonnes_communes = y1.columns.intersection(y2_df.columns)
    if len(colonnes_communes) == 0:
        return {
            "score_prediction": np.nan,
            "lag_prediction": None,
            "score_reaction": np.nan,
            "lag_reaction": None
        }

    s1, s2 = y1[colonnes_communes], y2_df[colonnes_communes]
    s1, s2 = s1.align(s2, join='inner')

    a = ((s1 - s1.mean()) / s1.std()).iloc[:, 0].to_numpy()
    b = ((s2 - s2.mean()) / s2.std()).iloc[:, 0].to_numpy()

    corr = np.correlate(a, b, mode='full') / len(a)
    lags = np.arange(-len(b) + 1, len(a))

    zero_lag_index = len(b) - 1

    # Filtrer les lags dans la fenêtre ±max_lag_days
    lag_mask = (lags >= -max_lag_days) & (lags <= max_lag_days)
    corr = corr[lag_mask]
    lags = lags[lag_mask]

    # Séparer lags négatifs (réaction) et positifs (prédiction)
    negative_mask = lags < 0
    positive_mask = lags >= 0

    negative_corr = corr[negative_mask]
    negative_lags = lags[negative_mask]

    positive_corr = corr[positive_mask]
    positive_lags = lags[positive_mask]

    # Score prédiction (lag >= 0)
    if len(positive_corr) > 0:
        idx_max_pos = np.argmax(positive_corr)
        score_prediction = (positive_corr[idx_max_pos] + 1) / 2 * 100
        lag_prediction = positive_lags[idx_max_pos]
    else:
        score_prediction = np.nan
        lag_prediction = None

    # Score réaction (lag < 0)
    if len(negative_corr) > 0:
        idx_max_neg = np.argmax(negative_corr)
        score_reaction = (negative_corr[idx_max_neg] + 1) / 2 * 100
        lag_reaction = negative_lags[idx_max_neg]
    else:
        score_reaction = np.nan
        lag_reaction = None

    return {
        "score_prediction": score_prediction,
        "lag_prediction": lag_prediction,
        "score_reaction": score_reaction,
        "lag_reaction": lag_reaction
    }

# --- MAIN ---
if __name__ == "__main__":
    ticker = "GOOG"

    # 1️⃣ Analyse du sentiment via Reddit (TextBlob)
    sentiment_df = main_analyse_textblob(ticker)

    if sentiment_df is None or sentiment_df.empty:
        print(f"⚠️ Aucune donnée d'analyse de sentiment disponible pour {ticker}.")
        exit()

    # Conversion du DataFrame en dict compatible
    y2_dict = {
        "GlobalScore": sentiment_df["GlobalScore"].tolist(),
        "analysis_date": sentiment_df["analysis_date"].astype(str).tolist()
    }

    # 2️⃣ Récupération du % de variation boursière
    y1 = get_pct_change_df(ticker)

    # Restreindre la période à celle du sentiment
    min_date = pd.to_datetime(min(y2_dict["analysis_date"]))
    max_date = pd.to_datetime(max(y2_dict["analysis_date"]))
    y1 = y1.loc[min_date:max_date]

    # 3️⃣ Calcul du score de compatibilité
    score = score_compatibilite_df(y1, y2_dict)
    print(score)
