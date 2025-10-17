import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from stock_data.dataframe_percent import get_pct_change_df  # Ton module perso
from sentiment_analysis_textblob import analyze_single_stock_textblob, analyze_single_stock_textblob, main_analyse_textblob   # Ton module perso


def score_compatibilite_df(y1: pd.DataFrame, y2: dict, col_name: str = None) -> float:
    """
    Calcule un score de compatibilité (0–100) entre un DataFrame y1 indexé par date
    et un dict y2 contenant 'GlobalScore' et 'analysis_date'.
    """
    if col_name is None:
        col_name = y1.columns[0]

    # Conversion dict -> DataFrame
    dates = pd.to_datetime(y2["analysis_date"])
    values = np.array(y2["GlobalScore"]) * 100 # Passage à l'échelle 0-100
    
    y2_df = pd.DataFrame(data={col_name: values}, index=dates)

    colonnes_communes = y1.columns.intersection(y2_df.columns)
    if len(colonnes_communes) == 0:
        print("⚠️ Pas de colonnes communes entre y1 et y2")
        return np.nan

    scores = []
    for col in colonnes_communes:
        s1, s2 = y1[col], y2_df[col]
        s1, s2 = s1.align(s2, join='inner')
        if len(s1) < 2:
            continue

        a = (s1 - s1.mean()) / s1.std()
        b = (s2 - s2.mean()) / s2.std()

        corr = np.correlate(a, b, mode='full') / len(a)
        r_max = np.max(corr)
        score = (r_max + 1) / 2 * 100
        scores.append(score)

    if not scores:
        print("⚠️ Pas assez de données valides pour calculer le score")
        return np.nan

    return np.mean(scores)


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
    print(f"Score de compatibilité moyen : {score:.2f}/100")

    # 4️⃣ Visualisation
    plt.figure(figsize=(12, 6))
    plt.plot(y1.index, y1.iloc[:, 0], label=f"{y1.columns[0]} (% de variation réelle)")
    plt.plot(pd.to_datetime(y2_dict["analysis_date"]), y2_dict["GlobalScore"], label="Sentiment Reddit (GlobalScore)")
    plt.title(f"{ticker} - Score de compatibilité : {score:.2f}/100")
    plt.xlabel("Date")
    plt.ylabel("Valeur")
    plt.legend()
    plt.grid(True)
    plt.show()
