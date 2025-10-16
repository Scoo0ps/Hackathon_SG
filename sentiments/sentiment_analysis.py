import pandas as pd
import numpy as np
import os
import tensorflow as tf

# Importer le modèle et le tokenizer chargés dans finbert_model.py
from finbert_model import model, tokenizer


# La fonction aggregate_sentiment_scores prend en paramètre une liste de scores de sentiment pour chaque texte d'entreprise
# et elle renvoie la moyenne de ces scores pour chaque catégorie de sentiment (Négatif, Neutre, Positif).
# L'objectif de cette fonction est d'obtenir un sentiment global par entreprise à partir des commentaires.

def aggregate_sentiment_scores(sentiment_scores):
    return sentiment_scores.mean(axis=0)    #axis=0 permet de faire une moyenne colonne par colonne




# La fonction analyze_sentiment prend en paramètre une liste de textes pour une entreprise et elle renvoie un dictionnaire
# avec les 3 robabilités et le score global (Positif - Négatif).
#
# Pour ce faire, elle suit ces étapes :
# 1. Elle vérifie qu'il y a bien des textes à analyser.
# 2. Elle transforme les textes en tokens compréhensibles par le modèle FinBERT.
# 3. Le modèle prédit les scores de sentiment pour chaque texte.
# 4. On convertit les scores en probabilités avec la fonction softmax.
# 5. On agrège les scores en prenant la moyenne pour chaque catégorie de sentiment.
# 6. On calcule le score global en soustrayant la probabilité Négative de la probabilité Positive.

def analyze_sentiment(texts):
    if not texts:
        return None
    # Tokenisation et prédiction
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='tf')
    outputs = model(**inputs)
    scores = tf.nn.softmax(outputs.logits, axis=-1).numpy()
    
    # Agrégation par moyenne
    aggregated_scores = aggregate_sentiment_scores(scores)
    
    # Score global = Positive - Negative
    global_score = float(aggregated_scores[2] - aggregated_scores[0])
    
    return {
        'Negative': float(aggregated_scores[0]),
        'Neutral': float(aggregated_scores[1]),
        'Positive': float(aggregated_scores[2]),
        'GlobalScore': global_score
    }




# La fonction analyse_csv prend en paramètre le chemin d'un fichier CSV, le nom de la colonne texte (content)
# et la colonne entreprise (stock_symbol) et elle renvoi en dictionnaire avec le sentiment pour chaque entreprise.
#
# Pour ce faire, elle suit ces étapes :
# 1. Elle vérifie que le fichier existe.
# 2. Elle charge le CSV dans un DataFrame pandas.
# 3. Elle vérifie que les colonnes texte et entreprise existent dans le DataFrame.
# 4. Elle groupe les données par entreprise et analyse le sentiment pour chaque groupe de textes.

def analyze_csv(file_path, text_column='content', symbol_column='stock_symbol'):
    """ Analyse un CSV et renvoie un dictionnaire avec le sentiment pour chaque action """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")
    
    df = pd.read_csv(file_path)
    
    if text_column not in df.columns or symbol_column not in df.columns:
        raise ValueError(f"Les colonnes '{text_column}' ou '{symbol_column}' n'existent pas dans le CSV")
    
    sentiment_results = {}
    for stock, group in df.groupby(symbol_column):
        texts = group[text_column].dropna().tolist()
        sentiment_results[stock] = analyze_sentiment(texts)
    
    return sentiment_results




if __name__ == "__main__":
    file_path = "../reddit_stock_data_20251016_114603.csv"
    sentiment_by_stock = analyze_csv(file_path, text_column='content', symbol_column='stock_symbol')
    
    for stock, sentiment in sentiment_by_stock.items():
        print(f"{stock}: {sentiment}")
