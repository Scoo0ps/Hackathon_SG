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
# avec les 3 probabilités et le score global (Positif - Négatif).
#
# Pour ce faire, elle suit ces étapes :
# 1. Elle vérifie qu'il y a bien des textes à analyser.
# 2. Elle compte le nombre de messages.
# 3. Elle transforme les textes en tokens compréhensibles par le modèle FinBERT.
# 4. Le modèle prédit les scores de sentiment pour chaque texte.
# 5. On convertit les scores en probabilités avec la fonction softmax.
# 6. On agrège les scores en prenant la moyenne pour chaque catégorie de sentiment.
# 7. On calcule le score global en soustrayant la probabilité Négative de la probabilité Positive.

def analyze_sentiment(texts, batch_size=32):
    if not texts:
        return None

    # Nombre de messages
    message_count = len(texts)
    all_scores= []

    # Traitement par batch pour éviter les problèmes de mémoire
    for i in range(0, message_count, batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='tf')
        outputs = model(**inputs)
        scores = tf.nn.softmax(outputs.logits, axis=-1).numpy()
        all_scores.append(scores)

    # On concatène tous les scores
    all_scores = np.concatenate(all_scores, axis=0)

    # Moyenne des scores
    aggregated_scores = aggregate_sentiment_scores(all_scores)
    
    # Score global = Positive - Negative
    global_score = float(aggregated_scores[2] - aggregated_scores[0])
    
    return {
        'Negative': float(aggregated_scores[0]),
        'Neutral': float(aggregated_scores[1]),
        'Positive': float(aggregated_scores[2]),
        'GlobalScore': global_score,
        'MessageCount': message_count
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
    file_path = "../reddit_stock_data_20251016_154138.csv"
    sentiment_by_stock = analyze_csv(file_path, text_column='content', symbol_column='stock_symbol')
    
    for stock, sentiment in sentiment_by_stock.items():
        print(f"{stock}: {sentiment}")

