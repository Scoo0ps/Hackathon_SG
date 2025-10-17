import pandas as pd
from sentiment_analysis_finbert import analyze_sentiment, load_finbert_model
from sentiment_analysis_textblob import analyze_sentiment_textblob
from reddit_scraper_quick import RedditStockScraper

def analyze_single_stock_mixed(ticker):

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
        texts_reddit = group[group['source'] == 'Reddit']['content'].dropna().tolist()
        texts_bloomberg = group[group['source'] == 'Bloomberg']['content'].dropna().tolist()

        # Analyse Reddit avec TextBlob
        reddit_result = analyze_sentiment_textblob(texts_reddit) if texts_reddit else None
        # Analyse Bloomberg avec FinBERT
        bloomberg_result = analyze_sentiment(texts_bloomberg) if texts_bloomberg else None

        # Si aucune donnée n'est disponible pour cette journée, on passe
        if not reddit_result and not bloomberg_result:
            continue

        # Création de la ligne de résultat en combinant les deux sources
        result_row = {
            'stock_symbol': ticker,
            'company_name': df['company_name'].iloc[0] if 'company_name' in df.columns else ticker,
            'NbReddit': nb_reddit,
            'NbBloomberg': nb_bloomberg,
            'analysis_date': day
        }

        # Ajouter les scores Reddit si disponibles
        if reddit_result:
            result_row.update({
                'Reddit_GlobalScore': reddit_result['GlobalScore'],
                'Reddit_MessageCount': reddit_result['MessageCount']
            })
        else:
            result_row.update({
                'Reddit_GlobalScore': None,
                'Reddit_MessageCount': 0
            })

        # Ajouter les scores Bloomberg si disponibles
        if bloomberg_result:
            result_row.update({
                'Bloomberg_Negative': bloomberg_result['Negative'],
                'Bloomberg_Neutral': bloomberg_result['Neutral'],
                'Bloomberg_Positive': bloomberg_result['Positive'],
                'Bloomberg_GlobalScore': bloomberg_result['GlobalScore'],
                'Bloomberg_MessageCount': bloomberg_result['MessageCount']
            })
        else:
            result_row.update({
                'Bloomberg_Negative': None,
                'Bloomberg_Neutral': None,
                'Bloomberg_Positive': None,
                'Bloomberg_GlobalScore': None,
                'Bloomberg_MessageCount': 0
            })

        daily_results.append(result_row)

    if not daily_results:
        print(f"Aucun résultat journalier pour {ticker}.")
        return None

    return pd.DataFrame(daily_results)


def main_analyse_mixed(ticker):
    result_df = analyze_single_stock_mixed(ticker)
    if result_df is not None:
        print(f"Résultats de l'analyse mixte pour {ticker} :")
        print(result_df)
        return result_df
    else:
        print(f"Aucun résultat d'analyse mixte pour {ticker}.")
        return None


if __name__ == "__main__":
    ticker = "AAPL"
    main_analyse_mixed(ticker)
