from scrape_finance_articles import scrape_bloomberg, convert_timestamp
from reddit_scraper_quick import RedditStockScraper
import pandas as pd
from playwright.sync_api import sync_playwright
from stock_keywords import STOCK_KEYWORDS, get_company_from_ticker


def scrape(ticker:str, days_back:int=30, max_workers:int=8) -> pd.DataFrame:

    # initialize Reddit scraper
    reddit_scraper = RedditStockScraper(days_back=days_back, max_workers=max_workers)
    
    # Search for single stock
    reddit_df = reddit_scraper.search_single_stock(ticker, limit_per_sub=20, time_filter='month')

    with sync_playwright() as playwright:
        bloomberg_df = scrape_bloomberg(playwright, get_company_from_ticker(ticker))
    
    # Combine dataframes
    combined_df = pd.concat([reddit_df, bloomberg_df], ignore_index=True)

    return combined_df

if __name__ == "__main__":
    ticker = "AAPL"
    combined_articles_df = scrape(ticker)
    print(combined_articles_df["content"])
    bloomberg_nb = combined_articles_df[combined_articles_df["source"] == "bloomberg"].shape[0]
    reddit_nb = combined_articles_df[combined_articles_df["source"] == "reddit"].shape[0]

    print(f"Bloomberg articles: {bloomberg_nb}, Reddit articles: {reddit_nb}")