import tensorflow as tf
from transformers import TFBertForSequenceClassification, BertTokenizer, set_seed
import pandas as pd
import numpy as np
import os
import tensorflow as tf


# Variables globales pour le modèle et le tokenizer
model = None
tokenizer = None

def load_finbert_model():
    global model, tokenizer
    if model is None or tokenizer is None:
        print("Chargement du modèle FinBERT...")
        set_seed(1, True)
        model_path = "ProsusAI/finbert"
        tokenizer = BertTokenizer.from_pretrained(model_path)
        model = TFBertForSequenceClassification.from_pretrained(model_path)
    else:
        print("Le modèle FinBERT est déjà chargé.")
    return model, tokenizer


from reddit_scraper_quick import RedditStockScraper


# La fonction aggregate_sentiment_scores prend en paramètre une liste de scores de sentiment pour plusieurs textes
# d'une même entreprise et elle renvoie la moyenne de ces scores pour chaque catégorie de sentiment (Négatif, Neutre, Positif).
# L'objectif de cette fonction est d'obtenir un sentiment global par entreprise à partir des commentaires.

def aggregate_sentiment_scores(sentiment_scores):
    return sentiment_scores.mean(axis=0)    #axis=0 permet de faire une moyenne colonne par colonne




# La fonction analyse_sentiment prend en paramètre une liste de textes et un batch_size (afin d'éviter un problème de mémoire).
# Elle renvoie un dictionnaire contenant les scores agrégés pour chaque catégorie de sentiment (Négatif, Neutre, Positif),
# le score global (Positif - Négatif) et le nombre de messages analysés.

def analyze_sentiment(texts, batch_size=32):

    # On vérifie que la liste de textes n'est pas vide
    if not texts:
        return None

    load_finbert_model()

    # On compte le nombre de messages
    message_count = len(texts)
    all_scores= []

    # Traitement par batch pour éviter les problèmes de mémoire
    for i in range(0, message_count, batch_size):
        batch_texts = texts[i:i+batch_size]
        # On tokenize les textes du batch afin de les préparer pour le modèle
        inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='tf')
        # On passe les inputs au modèle pour obtenir les scores de sentiment
        outputs = model(**inputs)
        # On applique la fonction softmax pour obtenir des probabilités
        scores = tf.nn.softmax(outputs.logits, axis=-1).numpy()
        # On stocke les scores de ce batch
        all_scores.append(scores)

    # On concatène tous les scores pour obtenir un seul tableau (avec une ligne par message et une colonne par catégorie de sentiment)
    all_scores = np.concatenate(all_scores, axis=0)

    # Moyenne des scores
    aggregated_scores = aggregate_sentiment_scores(all_scores)

    # Score global = Positive - Negative
    # Si le score global est >0, le sentiment global est plutôt positif, s'il est <0, il est plutôt négatif
    global_score = float(aggregated_scores[2] - aggregated_scores[0])

    return {
        'Negative': float(aggregated_scores[0]),
        'Neutral': float(aggregated_scores[1]),
        'Positive': float(aggregated_scores[2]),
        'GlobalScore': global_score,
        'MessageCount': message_count
    }




# La fonction analyze_single_stock prend en paramètre un ticker boursier,
# elle utilise le RedditStockScraper pour récupérer les messages Reddit liés à ce ticker,
# puis elle analyse le sentiment de ces messages jour par jour en utilisant la fonction analyze_sentiment.
# Elle renvoie un DataFrame contenant les résultats de l'analyse de sentiment pour chaque jour.

def analyze_single_stock(ticker):
    scraper = RedditStockScraper(days_back=30, max_workers=8)

    df = scraper.search_single_stock(ticker, limit_per_sub=20, time_filter='month')

    if df.empty:
        print(f"Aucune donnée trouvée pour le ticker {ticker}.")
        return None

    df['created_utc'] = pd.to_datetime(df['created_utc']).dt.date

    counts = df['source'].value_counts()
    nb_reddit = counts.get('Reddit', 0)
    nb_bloomberg = counts.get('Bloomberg', 0)

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
            'NbReddit': nb_reddit,
            'NbBloomberg': nb_bloomberg,
            'analysis_date': day           
        })

    if not daily_results:
        print(f"Aucun résultat journalier pour {ticker}.")
        return None

    result_df = pd.DataFrame(daily_results)
    return result_df



# La fonction main_analyse_finbert prend en paramètre un ticker boursier,
# elle appelle la fonction analyze_single_stock pour obtenir les résultats de l'analyse de sentiment,
# puis elle affiche ces résultats ou un message indiquant qu'aucun résultat n'a été trouvé.

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