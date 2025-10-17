 import tensorflow as tf
from transformers import TFBertForSequenceClassification, BertTokenizer, set_seed
import pandas as pd
import numpy as np
import os
import tensorflow as tf


# On commence par charger le modèle

# Fixer la seed pour la reproductibilité (une seule fois)
set_seed(1, True)

# Charger le modèle et le tokenizer FinBERT (une seule fois)
model_path = "ProsusAI/finbert"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = TFBertForSequenceClassification.from_pretrained(model_path)


from reddit_scraper_quick import RedditStockScraper


# La fonction aggregate_sentiment_scores prend en paramètre une liste de scores de sentiment pour chaque texte d'entreprise
# et elle renvoie la moyenne de ces scores pour chaque catégorie de sentiment (Négatif, Neutre, Positif).
# L'objectif de cette fonction est d'obtenir un sentiment global par entreprise à partir des commentaires.

def aggregate_sentiment_scores(sentiment_scores):
    return sentiment_scores.mean(axis=0)    #axis=0 permet de faire une moyenne colonne par colonne






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





def analyze_single_stock(ticker):
    scraper = RedditStockScraper(days_back=30, max_workers=8)

    df = scraper.search_single_stock(ticker, limit_per_sub=20, time_filter='month')

    if df.empty:
        print(f"Aucune donnée trouvée pour le ticker {ticker}.")
        return None

    df['created_utc'] = pd.to_datetime(df['created_utc']).dt.date

    daily_results = []

    for day, group in df.groupby('created_utc'):
        texts = group['content'].dropna().tolist()
        if not texts:
            continue

        sentiment_result = analyze_sentiment(texts)
        if sentiment_result is None:
            continue

        daily_results.append({
            'stock_symbol': ticker,
            'company_name': df['company_name'].iloc[0] if 'company_name' in df.columns else ticker,
            'Negative': sentiment_result['Negative'],
            'Neutral': sentiment_result['Neutral'],
            'Positive': sentiment_result['Positive'],
            'GlobalScore': sentiment_result['GlobalScore'],
            'MessageCount': sentiment_result['MessageCount'],
            'analysis_date': day
        })

    if not daily_results:
        print(f"Aucun résultat journalier pour {ticker}.")
        return None

    result_df = pd.DataFrame(daily_results)
    return result_df



def main_analyse_finbert(ticker):
    result_df = analyze_single_stock(ticker)
    if result_df is not None:
        print(f"Résultats de l'analyse de sentiment pour {ticker} :")
        print(result_df)
        return result_df
    else:
        print(f"Aucun résultat d'analyse de sentiment pour {ticker}.")


if __name__ == "__main__":
    ticker = "AAPL"
    main_analyse_finbert(ticker)