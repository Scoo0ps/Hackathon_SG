import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from stock_data.dataframe_percent import get_pct_change_df  # Ton import perso


def score_compatibilite_df(y1: pd.DataFrame, y2: dict, col_name: str = None) -> float:
    """
    Calcule un score de compatibilité (0–100) entre un DataFrame y1 indexé par date
    et un dict y2 contenant au moins 'GlobalScore' et 'analysis_date'.

    La conversion dict → DataFrame est automatique dans la fonction.

    Paramètres
    ----------
    y1 : pd.DataFrame
        DataFrame indexé par date, avec une ou plusieurs colonnes.
    y2 : dict
        Dictionnaire avec au moins les clés 'GlobalScore' (liste/array)
        et 'analysis_date' (liste/array de dates).
    col_name : str, optionnel
        Nom de la colonne à utiliser pour y2 (par défaut, première colonne de y1).

    Retour
    -------
    float
        Score moyen de compatibilité entre 0 et 100, ou np.nan si pas calculable.
    """

    # Déterminer le nom de colonne à utiliser dans y2
    if col_name is None:
        col_name = y1.columns[0]

    # Conversion dict y2 en DataFrame
    dates = pd.to_datetime(y2["analysis_date"])
    values = y2["GlobalScore"]
    y2_df = pd.DataFrame(data={col_name: values}, index=dates)

    # Colonnes communes
    colonnes_communes = y1.columns.intersection(y2_df.columns)
    if len(colonnes_communes) == 0:
        print("⚠️ Pas de colonnes communes entre y1 et y2")
        return np.nan

    scores = []
    for col in colonnes_communes:
        s1 = y1[col]
        s2 = y2_df[col]

        # Aligner sur dates communes
        s1, s2 = s1.align(s2, join='inner')
        if len(s1) < 2:
            continue

        a = s1.to_numpy(dtype=float)
        b = s2.to_numpy(dtype=float)

        a = (a - np.mean(a)) / np.std(a)
        b = (b - np.mean(b)) / np.std(b)

        corr = np.correlate(a, b, mode='full') / len(a)
        r_max = np.max(corr)

        score = (r_max + 1) / 2 * 100
        scores.append(score)

    if len(scores) == 0:
        print("⚠️ Pas assez de données valides pour calculer le score")
        return np.nan

    return np.mean(scores)


# --- TEST ---

if __name__ == "__main__":
    # Chargement données réelles Apple
    y1 = get_pct_change_df("AAPL")


    dates_30 = y1.index[-30:]
    y2_dict = {
        "GlobalScore": np.sin(np.linspace(0, 4 * np.pi, len(dates_30)) - 1.5).tolist(),
        "analysis_date": dates_30.strftime("%Y-%m-%d").tolist()
    }

    # Calcul du score (conversion dict intégrée)
    score = score_compatibilite_df(y1.loc[dates_30], y2_dict)
    print(f"Score de compatibilité moyen sur les 30 derniers jours : {score:.2f}/100")

    # Visualisation
    plt.figure(figsize=(12, 6))
    plt.plot(y1.loc[dates_30].index, y1.loc[dates_30].iloc[:, 0], label=f"{y1.columns[0]} (réel)")
    plt.plot(pd.to_datetime(y2_dict["analysis_date"]), y2_dict["GlobalScore"], label="GlobalScore (dict synthétique)")
    plt.title(f"Score de compatibilité (30 derniers jours) : {score:.2f}/100")
    plt.xlabel("Date")
    plt.ylabel("Valeurs")
    plt.legend()
    plt.grid(True)
    plt.show()
