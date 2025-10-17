import praw
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import time
import concurrent.futures
from threading import Lock
from stock_keywords import STOCK_KEYWORDS

load_dotenv()

class RedditStockScraper:
    def __init__(self, days_back=7, max_workers=10):
        """Initialize Reddit API connection with comprehensive stock keywords"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'StockScraper/1.0')
        )
        
        # Load stock keywords from external file
        self.stock_keywords = STOCK_KEYWORDS
        
        # Financial subreddits
        self.financial_subreddits = [
            'investing', 'stocks', 
            'StockMarket', 'wallstreetbets', 
            'options', 'eupersonalfinance', 'france', 'europe'
        ]
        
        # Time filtering
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.scraped_data = []
        
        # Threading
        self.max_workers = max_workers
        self.data_lock = Lock()
    
    def is_recent(self, timestamp):
        """Check if post/comment is within time range"""
        post_date = datetime.fromtimestamp(timestamp)
        return post_date >= self.cutoff_date
    
    def create_search_query(self, ticker, use_context=False):
        """Create optimized search query for Reddit"""
        keywords = self.stock_keywords[ticker]["primary"].copy()
        
        if use_context:
            keywords.extend(self.stock_keywords[ticker]["context"][:3])
        
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
        return query
    
    def detect_stock_in_text(self, text, ticker):
        """Check if text mentions the stock using all keywords"""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Check primary keywords
        for keyword in self.stock_keywords[ticker]["primary"]:
            pattern = rf'\b{re.escape(keyword.lower())}\b'
            if re.search(pattern, text_lower):
                return True
        
        # Check context keywords
        for keyword in self.stock_keywords[ticker]["context"]:
            pattern = rf'\b{re.escape(keyword.lower())}\b'
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def get_full_post_text(self, submission):
        """Combine title and content for complete text analysis"""
        title = submission.title or ""
        content = submission.selftext or ""
        return f"{title} {content}"
    
    def process_submission(self, submission, ticker):
        """Process a Reddit submission and its comments"""
        submission_data = {
            'message_id': submission.id,
            'type': 'post',
            'subreddit': submission.subreddit.display_name,
            'stock_symbol': ticker,
            'company_name': self.stock_keywords[ticker]["company"],
            'title': submission.title,
            'content': submission.selftext,
            'author': str(submission.author) if submission.author else '[deleted]',
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'created_utc': datetime.fromtimestamp(submission.created_utc),
            'url': submission.url,
            'permalink': f"https://reddit.com{submission.permalink}"
        }
        
        with self.data_lock:
            self.scraped_data.append(submission_data)
        
        # Process comments in a separate thread
        self.process_comments(submission, ticker)
    
    def process_comments(self, submission, ticker):
        """Process comments from a submission"""
        try:
            submission.comments.replace_more(limit=0)
            
            comments_data = []
            for comment in submission.comments.list():
                if hasattr(comment, 'body') and self.is_recent(comment.created_utc):
                    if self.detect_stock_in_text(comment.body, ticker):
                        comment_data = {
                            'message_id': comment.id,
                            'type': 'comment',
                            'subreddit': submission.subreddit.display_name,
                            'stock_symbol': ticker,
                            'company_name': self.stock_keywords[ticker]["company"],
                            'title': submission.title,
                            'content': comment.body,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'score': comment.score,
                            'upvote_ratio': None,
                            'num_comments': None,
                            'created_utc': datetime.fromtimestamp(comment.created_utc),
                            'url': submission.url,
                            'permalink': f"https://reddit.com{comment.permalink}"
                        }
                        comments_data.append(comment_data)
            
            # Add all comments at once with thread safety
            if comments_data:
                with self.data_lock:
                    self.scraped_data.extend(comments_data)
                    
        except Exception as e:
            print(f"    Error processing comments: {str(e)}")
    
    def search_single_subreddit(self, args):
        """Search a single subreddit (for threading)"""
        subreddit_name, ticker, limit, time_filter = args
        print(f"  Searching r/{subreddit_name} for {ticker}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            search_query = self.create_search_query(ticker, use_context=False)
            
            for submission in subreddit.search(
                query=search_query, 
                time_filter=time_filter, 
                limit=limit, 
                sort='relevance'
            ):
                if self.is_recent(submission.created_utc):
                    full_text = self.get_full_post_text(submission)
                    if self.detect_stock_in_text(full_text, ticker):
                        self.process_submission(submission, ticker)
            
            print(f"  ✅ Finished r/{subreddit_name}")
            
        except Exception as e:
            print(f"    Error in r/{subreddit_name}: {str(e)}")
    
    def search_single_stock(self, ticker, limit_per_sub=50, time_filter='week'):
        """
        Search for a SINGLE specific stock using threading
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MC.PA')
            limit_per_sub: Number of posts to search per subreddit
            time_filter: Reddit time filter ('hour', 'day', 'week', 'month', 'year')
        
        Returns:
            pandas DataFrame with results
        """
        # Validate ticker
        if ticker not in self.stock_keywords:
            print(f"❌ Error: '{ticker}' not found in stock keywords database")
            print(f"Available tickers: {', '.join(list(self.stock_keywords.keys()))}")
            return pd.DataFrame()
        
        print(f"\n{'='*60}")
        print(f"Searching Reddit for {ticker}")
        print(f"Company: {self.stock_keywords[ticker]['company']}")
        print(f"Period: Last {self.days_back} days")
        print(f"Threads: {self.max_workers}")
        print(f"{'='*60}\n")
        
        # Clear previous data
        self.scraped_data = []
        
        # Prepare arguments for threading
        search_args = [
            (subreddit, ticker, limit_per_sub, time_filter) 
            for subreddit in self.financial_subreddits
        ]
        
        # Use ThreadPoolExecutor for concurrent execution
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = [executor.submit(self.search_single_subreddit, args) for args in search_args]
            
            # Wait for all to complete
            completed, not_completed = concurrent.futures.wait(
                futures, 
                timeout=300,  # 5 minute timeout
                return_when=concurrent.futures.ALL_COMPLETED
            )
            
            if not_completed:
                print(f"⚠️  {len(not_completed)} subreddit searches timed out")
        
        elapsed_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ Search Complete: {len(self.scraped_data)} messages found for {ticker}")
        print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
        print(f"{'='*60}\n")
        
        return self.get_dataframe()
    
    def search_multiple_stocks(self, tickers, limit_per_sub=30, time_filter='week'):
        """
        Search for MULTIPLE stocks concurrently
        
        Args:
            tickers: List of stock ticker symbols
            limit_per_sub: Number of posts to search per subreddit
            time_filter: Reddit time filter
        
        Returns:
            Dictionary with ticker as key and DataFrame as value
        """
        print(f"\n{'='*60}")
        print(f"Searching Reddit for {len(tickers)} stocks")
        print(f"Stocks: {', '.join(tickers)}")
        print(f"Threads: {self.max_workers}")
        print(f"{'='*60}\n")
        
        results = {}
        
        def search_stock_wrapper(ticker):
            """Wrapper function for threading individual stock searches"""
            self.scraped_data = []  # Reset for each stock
            df = self.search_single_stock(ticker, limit_per_sub, time_filter)
            return ticker, df
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(tickers))) as executor:
            futures = {executor.submit(search_stock_wrapper, ticker): ticker for ticker in tickers}
            
            for future in concurrent.futures.as_completed(futures):
                ticker = futures[future]
                try:
                    ticker, df = future.result()
                    results[ticker] = df
                    print(f"✅ Completed {ticker}: {len(df)} messages")
                except Exception as e:
                    print(f"❌ Error searching {ticker}: {str(e)}")
                    results[ticker] = pd.DataFrame()
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Total time for {len(tickers)} stocks: {elapsed_time:.2f} seconds")
        
        return results
    
    def get_dataframe(self):
        """Convert scraped data to pandas DataFrame"""
        if not self.scraped_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.scraped_data)
        df = df.drop_duplicates(subset=['message_id'])
        df = df.sort_values('created_utc', ascending=False)
        df['source'] = 'reddit'
        return df
    
    def save_to_csv(self, df=None, filename=None):
        """Save scraped data to CSV file"""
        if df is None:
            df = self.get_dataframe()
        
        if df.empty:
            print("No data to save.")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ticker = df['stock_symbol'].iloc[0] if len(df) > 0 else 'stock'
            filename = f"reddit_{ticker}_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"💾 Data saved to {filename}")
        return df
    
    def save_multiple_to_csv(self, results_dict, base_filename=None):
        """Save multiple stock results to separate CSV files"""
        if not base_filename:
            base_filename = f"reddit_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        saved_files = {}
        for ticker, df in results_dict.items():
            if not df.empty:
                filename = f"{base_filename}_{ticker}.csv"
                df.to_csv(filename, index=False)
                saved_files[ticker] = filename
                print(f"💾 {ticker} data saved to {filename}")
        
        return saved_files
    
    def print_summary(self, df=None):
        """Print formatted summary"""
        if df is None:
            df = self.get_dataframe()
        
        if df.empty:
            print("No data scraped yet.")
            return
        
        print("\n" + "="*60)
        print("📈 SCRAPING SUMMARY")
        print("="*60)
        print(f"Total messages: {len(df)}")
        print(f"Posts: {len(df[df['type'] == 'post'])}")
        print(f"Comments: {len(df[df['type'] == 'comment'])}")
        print(f"\nSubreddits:")
        for subreddit, count in df['subreddit'].value_counts().head(10).items():
            print(f"  r/{subreddit}: {count}")
        print(f"\nDate range: {df['created_utc'].min()} to {df['created_utc'].max()}")
        print("="*60 + "\n")


def main():
    # Single stock search
    ticker = "MSFT"
    
    # Initialize scraper with more workers for better performance
    scraper = RedditStockScraper(days_back=30, max_workers=8)
    
    # Search for single stock
    df = scraper.search_single_stock(ticker, limit_per_sub=20, time_filter='month')
    
    # Save and display results
    if not df.empty:
        scraper.save_to_csv(df)
        scraper.print_summary(df)
        
        # Display sample data
        print("📋 SAMPLE DATA (First 10 rows):")
        print(df[['stock_symbol', 'company_name', 'type', 'author', 'created_utc', 'score']].head(10))
        
        # Show top posts
        print("\n🔥 TOP POSTS:")
        top_posts = df[df['type'] == 'post'].nlargest(5, 'score')
        for idx, row in top_posts.iterrows():
            print(f"\n  [{row['score']} points] {row['title']}")
            print(f"  r/{row['subreddit']} | {row['created_utc'].strftime('%Y-%m-%d')}")
    else:
        print(f"❌ No data found for {ticker}")


if __name__ == "__main__":
    # Run single stock search
    main()