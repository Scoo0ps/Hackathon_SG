import pandas as pd
import numpy as np
import os
import tensorflow as tf

# Importer le modèle et le tokenizer chargés une seule fois
from finbert_model import model, tokenizer

def aggregate_sentiment_scores(sentiment_scores):
    """ Agrège les scores de sentiment en faisant la moyenne """
    return sentiment_scores.mean(axis=0)

def analyze_sentiment(texts):
    """ Analyse le sentiment d'une liste de textes et retourne les 3 probabilités + score global """
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

# Exemple d'utilisation
if __name__ == "__main__":
    file_path = "../reddit_stock_data_20251016_114603.csv"  # Remplacer par ton CSV
    sentiment_by_stock = analyze_csv(file_path, text_column='content', symbol_column='stock_symbol')
    
    for stock, sentiment in sentiment_by_stock.items():
        print(f"{stock}: {sentiment}")
