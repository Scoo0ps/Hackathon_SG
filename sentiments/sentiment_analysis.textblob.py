import pandas as pd
import numpy as np
import os
from textblob import TextBlob



def analyze_sentiment_textblob(texts):
    if not texts:
        return None

    polarities = [TextBlob(str(t)).sentiment.polarity for t in texts]
    message_count = len(polarities)

    negative_mask = np.array(polarities) < -0.05
    positive_mask = np.array(polarities) > 0.05
    neutral_mask = ~(negative_mask | positive_mask)

    # Déterminer les proportions
    negative_ratio = np.mean(negative_mask)
    neutral_ratio = np.mean(neutral_mask)
    positive_ratio = np.mean(positive_mask)

    # Score global = moyenne des polarités
    global_score = float(positive_ratio - negative_ratio)

    return {
        'Negative': float(negative_ratio),
        'Neutral': float(neutral_ratio),
        'Positive': float(positive_ratio),
        'GlobalScore': global_score,
        'MessageCount': message_count
    }



# La fonction analyze_csv_textblob prend en paramètre le chemin d'un fichier CSV, le nom de la colonne de texte
# et le nom de la colonne de symbole boursier.
# Elle lit le CSV, groupe les textes par symbole boursier et applique la fonction analyze_sentiment_textblob à chaque groupe.
# Elle renvoie un dictionnaire avec le symbole boursier comme clé et les résultats d'analyse de sentiment comme valeur.

def analyze_csv_textblob(file_path, text_column='content', symbol_column='stock_symbol'):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")

    df = pd.read_csv(file_path)

    if text_column not in df.columns or symbol_column not in df.columns:
        raise ValueError(f"Les colonnes '{text_column}' ou '{symbol_column}' n'existent pas dans le CSV")

    sentiment_results = {}
    for stock, group in df.groupby(symbol_column):
        texts = group[text_column].dropna().tolist()
        sentiment_results[stock] = analyze_sentiment_textblob(texts)

    return sentiment_results


if __name__ == "__main__":
    file_path = "../reddit_stock_data_20251016_154138.csv"
    sentiment_by_stock = analyze_csv_textblob(file_path, text_column='content', symbol_column='stock_symbol')

    for stock, sentiment in sentiment_by_stock.items():
        print(f"{stock}: {sentiment}")
