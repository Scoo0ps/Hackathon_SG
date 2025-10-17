import praw
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import time
from stock_keywords import STOCK_KEYWORDS
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

class RedditStockScraper:
    def __init__(self, days_back=7):
        """Initialize Reddit API connection with comprehensive stock keywords"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'StockScraper/1.0')
        )
        
        # Load stock keywords from external file
        self.stock_keywords = STOCK_KEYWORDS
        
        # Financial subreddits - OPTIMIZED: Remove less active ones for speed
        self.financial_subreddits = [
            'wallstreetbets',  # Most active first
            'stocks', 
            'investing',
            'StockMarket',
            'options',
            'eupersonalfinance',
            'france',
            'europe'
            # Removed less relevant: 'options', 'eupersonalfinance', 'france', 'europe'
        ]
        
        # Time filtering
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.scraped_data = []
        self.lock = threading.Lock()  # Thread-safe data collection
        
        # Compile regex patterns once for better performance
        self._compiled_patterns = {}
    
    def _get_compiled_pattern(self, keyword):
        """Cache compiled regex patterns for better performance"""
        if keyword not in self._compiled_patterns:
            self._compiled_patterns[keyword] = re.compile(
                rf'\b{re.escape(keyword.lower())}\b',
                re.IGNORECASE
            )
        return self._compiled_patterns[keyword]
    
    def is_recent(self, timestamp):
        """Check if post/comment is within time range"""
        post_date = datetime.fromtimestamp(timestamp)
        return post_date >= self.cutoff_date
    
    def create_search_query(self, ticker, use_context=False):
        """Create optimized search query for Reddit"""
        keywords = self.stock_keywords[ticker]["primary"].copy()
        
        if use_context:
            keywords.extend(self.stock_keywords[ticker]["context"][:3])
        
        # Use simpler query format for better performance
        query = " OR ".join(keywords[:3])  # Reduced to 3 keywords for faster search
        return query
    
    def detect_stock_in_text(self, text, ticker):
        """OPTIMIZED: Check if text mentions the stock using compiled regex"""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Check primary keywords (most important)
        for keyword in self.stock_keywords[ticker]["primary"]:
            pattern = self._get_compiled_pattern(keyword)
            if pattern.search(text_lower):
                return True
        
        # OPTIMIZATION: Skip context keywords for faster processing
        # Only check if no primary match found
        return False
    
    def get_full_post_text(self, submission):
        """Combine title and content for complete text analysis"""
        title = submission.title or ""
        content = submission.selftext or ""
        return f"{title} {content}"
    
    def search_stock_in_subreddit(self, subreddit_name, ticker, limit=50, time_filter='week'):
        """Search for a specific stock in a subreddit using keywords"""
        print(f"  Searching r/{subreddit_name} for {ticker}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            search_query = self.create_search_query(ticker, use_context=False)
            
            count = 0
            for submission in subreddit.search(query=search_query, 
                                             time_filter=time_filter, 
                                             limit=limit, 
                                             sort='relevance'):
                if self.is_recent(submission.created_utc):
                    full_text = self.get_full_post_text(submission)
                    if self.detect_stock_in_text(full_text, ticker):
                        self.process_submission(submission, ticker, process_comments=False)  # FASTER: Skip comments initially
                        count += 1
            
            print(f"    Found {count} posts")
            time.sleep(0.3)  # Reduced delay
            
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    def process_submission(self, submission, ticker, process_comments=True):
        """Process a Reddit submission and optionally its comments"""
        post_data = {
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
        
        # Thread-safe append
        with self.lock:
            self.scraped_data.append(post_data)
        
        # Process comments only if requested
        if process_comments:
            self.process_comments(submission, ticker)
    
    def process_comments(self, submission, ticker, max_comments=10):
        """OPTIMIZED: Process only top comments from a submission"""
        try:
            submission.comments.replace_more(limit=0)  # Don't expand "more comments"
            
            # Only process top N comments for speed
            comments = list(submission.comments)[:max_comments]
            
            for comment in comments:
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
                        
                        with self.lock:
                            self.scraped_data.append(comment_data)
        except Exception as e:
            print(f"    Error processing comments: {str(e)}")
    
    def search_single_stock_parallel(self, ticker, limit_per_sub=30, time_filter='week', max_workers=4):
        """
        FASTEST METHOD: Search using parallel threads
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MC.PA')
            limit_per_sub: Number of posts to search per subreddit
            time_filter: Reddit time filter ('hour', 'day', 'week', 'month', 'year')
            max_workers: Number of parallel threads (default 4)
        
        Returns:
            pandas DataFrame with results
        """
        # Validate ticker
        if ticker not in self.stock_keywords:
            print(f"❌ Error: '{ticker}' not found in stock keywords database")
            print(f"Available tickers: {', '.join(list(self.stock_keywords.keys()))}")
            return pd.DataFrame()
        
        print(f"\n{'='*60}")
        print(f"🚀 FAST PARALLEL SEARCH for {ticker}")
        print(f"Company: {self.stock_keywords[ticker]['company']}")
        print(f"Period: Last {self.days_back} days")
        print(f"Threads: {max_workers}")
        print(f"{'='*60}\n")
        
        # Clear previous data
        self.scraped_data = []
        
        start_time = time.time()
        
        # Search subreddits in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.search_stock_in_subreddit,
                    subreddit,
                    ticker, 
                    limit_per_sub, 
                    time_filter
                ): subreddit 
                for subreddit in self.financial_subreddits
            }
            
            for future in as_completed(futures):
                subreddit = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"  ❌ Error in r/{subreddit}: {str(e)}")
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ Search Complete: {len(self.scraped_data)} messages found for {ticker}")
        print(f"⏱️  Time elapsed: {elapsed_time:.2f} seconds")
        print(f"{'='*60}\n")
        
        return self.get_dataframe()
    
    def search_single_stock(self, ticker, limit_per_sub=30, time_filter='week'):
        """
        OPTIMIZED: Search for a SINGLE specific stock (sequential but optimized)
        
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
        print(f"Searching in: Title AND Content")
        print(f"{'='*60}\n")
        
        # Clear previous data
        self.scraped_data = []
        
        start_time = time.time()
        
        # Search in all financial subreddits
        for subreddit in self.financial_subreddits:
            self.search_stock_in_subreddit(subreddit, ticker, limit_per_sub, time_filter)
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ Search Complete: {len(self.scraped_data)} messages found for {ticker}")
        print(f"⏱️  Time elapsed: {elapsed_time:.2f} seconds")
        print(f"{'='*60}\n")
        
        return self.get_dataframe()
    
    def get_dataframe(self):
        """Convert scraped data to pandas DataFrame"""
        if not self.scraped_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.scraped_data)
        df = df.drop_duplicates(subset=['message_id'])
        df = df.sort_values('created_utc', ascending=False)
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
    ticker = "MSFT"

    # Initialize scraper
    scraper = RedditStockScraper(days_back=30)
    
    # METHOD 1: FASTEST - Parallel search (recommended)
    print("🚀 Using PARALLEL search (fastest)")
    df = scraper.search_single_stock_parallel(ticker, limit_per_sub=100, time_filter='month', max_workers=4)
    
    # METHOD 2: OPTIMIZED - Sequential search (slower but stable)
    # print("⚡ Using OPTIMIZED sequential search")
    # df = scraper.search_single_stock(ticker, limit_per_sub=30, time_filter='month')
    
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
    main()