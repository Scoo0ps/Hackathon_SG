import pandas as pd
import numpy as np
import os
from textblob import TextBlob

from reddit_scraper_quick import RedditStockScraper

def analyze_sentiment_textblob(texts):
    if not texts:
        return None

    polarities = [TextBlob(str(t)).sentiment.polarity for t in texts]
    message_count = len(polarities)

    # Score global = moyenne des polarités
    global_score = float(np.mean(polarities))

    return {
        'GlobalScore': global_score,
        'MessageCount': message_count
    }



def analyze_single_stock_textblob(ticker):
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

        sentiment_result = analyze_sentiment_textblob(texts)
        if sentiment_result is None:
            continue

        daily_results.append({
            'stock_symbol': ticker,
            'company_name': df['company_name'].iloc[0] if 'company_name' in df.columns else ticker,
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




def main_analyse_textblob(ticker):
    result_df = analyze_single_stock_textblob(ticker)
    if result_df is not None:
        print(f"Résultats de l'analyse de sentiment TextBlob pour {ticker} :")
        print(result_df)
        return result_df
    else:
        print(f"Aucun résultat d'analyse de sentiment TextBlob pour {ticker}.")
        return None


import time

if __name__ == "__main__":
    start = time.time()
    ticker = "AAPL"
    main_analyse_textblob(ticker)
    end = time.time()
    print(f"Temps d'exécution : {end - start} secondes")