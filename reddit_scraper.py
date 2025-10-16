import praw
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import time
from stock_keywords import STOCK_KEYWORDS, get_all_tickers

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
    
    def is_recent(self, timestamp):
        """Check if post/comment is within time range"""
        post_date = datetime.fromtimestamp(timestamp)
        return post_date >= self.cutoff_date
    
    def create_search_query(self, ticker, use_context=False):
        """Create optimized search query for Reddit"""
        keywords = self.stock_keywords[ticker]["primary"].copy()
        
        if use_context:
            # Add top context keywords for broader search
            keywords.extend(self.stock_keywords[ticker]["context"][:3])
        
        # Create OR query
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # Limit to 5 keywords
        return query
    
    def detect_stock_in_text(self, text, ticker):
        """Check if text mentions the stock using all keywords"""
        if not text:  # Handle empty text
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
    
    def search_stock_in_subreddit(self, subreddit_name, ticker, limit=50, time_filter='week'):
        """Search for a specific stock in a subreddit using keywords"""
        print(f"  Searching r/{subreddit_name} for {ticker}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            search_query = self.create_search_query(ticker, use_context=False)
            
            # Search using Reddit API
            for submission in subreddit.search(query=search_query, 
                                             time_filter=time_filter, 
                                             limit=limit, 
                                             sort='relevance'):
                if self.is_recent(submission.created_utc):
                    # Check BOTH title AND content for stock mentions
                    full_text = self.get_full_post_text(submission)
                    if self.detect_stock_in_text(full_text, ticker):
                        self.process_submission(submission, ticker)
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    def scrape_subreddit(self, subreddit_name, limit=100, time_filter='week'):
        """Scrape subreddit and detect all stocks in title AND content"""
        print(f"  Scraping r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts_processed = 0
            
            # Get hot and new posts
            for submission in list(subreddit.hot(limit=limit//2)) + list(subreddit.new(limit=limit//2)):
                if not self.is_recent(submission.created_utc):
                    continue
                
                posts_processed += 1
                # Get full text (title + content)
                full_text = self.get_full_post_text(submission)
                
                # Check all tickers in the FULL TEXT (not just title)
                for ticker in self.stock_keywords.keys():
                    if self.detect_stock_in_text(full_text, ticker):
                        self.process_submission(submission, ticker)
            
            print(f"    Processed {posts_processed} posts")
            time.sleep(1)
            
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    def process_submission(self, submission, ticker):
        """Process a Reddit submission and its comments"""
        # Add post data
        self.scraped_data.append({
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
        })
        
        # Process comments
        self.process_comments(submission, ticker)
    
    def process_comments(self, submission, ticker):
        """Process comments from a submission - check content only"""
        try:
            submission.comments.replace_more(limit=0)
            
            for comment in submission.comments.list():
                if hasattr(comment, 'body') and self.is_recent(comment.created_utc):
                    # Check if comment CONTENT mentions the stock
                    if self.detect_stock_in_text(comment.body, ticker):
                        self.scraped_data.append({
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
                        })
        except Exception as e:
            print(f"    Error processing comments: {str(e)}")
    
    def scrape_all_stocks(self, method='search', limit_per_sub=50, time_filter='week'):
        """
        Main scraping method
        method: 'search' (targeted keyword search) or 'detect' (scrape and detect)
        """
        print(f"\n{'='*60}")
        print(f"Starting Reddit Stock Scraping")
        print(f"Period: Last {self.days_back} days")
        print(f"Method: {method}")
        print(f"Searching in: Title AND Content")
        print(f"Stocks tracked: {len(self.stock_keywords)}")
        print(f"{'='*60}\n")
        
        if method == 'search':
            # Targeted search for each stock
            for ticker in self.stock_keywords.keys():
                print(f"\n🔍 Searching for {ticker} ({self.stock_keywords[ticker]['company']}):")
                for subreddit in self.financial_subreddits:
                    self.search_stock_in_subreddit(subreddit, ticker, limit_per_sub, time_filter)
        
        elif method == 'detect':
            # General scraping with detection
            for subreddit in self.financial_subreddits:
                print(f"\n📊 Scraping r/{subreddit}:")
                self.scrape_subreddit(subreddit, limit_per_sub*2, time_filter)
        
        print(f"\n{'='*60}")
        print(f"✅ Scraping Complete: {len(self.scraped_data)} messages found")
        print(f"{'='*60}\n")
    
    def get_dataframe(self):
        """Convert scraped data to pandas DataFrame"""
        if not self.scraped_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.scraped_data)
        # Remove duplicates
        df = df.drop_duplicates(subset=['message_id'])
        # Sort by date
        df = df.sort_values('created_utc', ascending=False)
        return df
    
    def save_to_csv(self, filename=None):
        """Save scraped data to CSV file"""
        df = self.get_dataframe()
        
        if df.empty:
            print("No data to save.")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_stock_data_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"💾 Data saved to {filename}")
        return df
    
    def get_summary(self):
        """Get summary statistics of scraped data"""
        df = self.get_dataframe()
        
        if df.empty:
            return "No data scraped yet."
        
        summary = {
            'Total messages': len(df),
            'Posts': len(df[df['type'] == 'post']),
            'Comments': len(df[df['type'] == 'comment']),
            'Unique stocks': df['stock_symbol'].nunique(),
            'Stock mentions': df['stock_symbol'].value_counts().to_dict(),
            'Subreddits': df['subreddit'].value_counts().to_dict(),
            'Date range': f"{df['created_utc'].min()} to {df['created_utc'].max()}",
            'Top authors': df['author'].value_counts().head(5).to_dict()
        }
        
        return summary
    
    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()
        
        if isinstance(summary, str):
            print(summary)
            return
        
        print("\n" + "="*60)
        print("📈 SCRAPING SUMMARY")
        print("="*60)
        
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in list(value.items())[:10]:  # Limit to top 10
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
        
        print("="*60 + "\n")


def main():
    """Main execution function"""
    
    # Method 1: Targeted keyword search (RECOMMENDED - Most Precise)
    print("🎯 METHOD 1: Targeted Keyword Search (Title + Content)")
    scraper = RedditStockScraper(days_back=30)
    scraper.scrape_all_stocks(method='search', limit_per_sub=30, time_filter='month')
    
    # Save and display results
    df = scraper.save_to_csv()
    scraper.print_summary()
    
    # Display sample data
    if df is not None and not df.empty:
        print("\n📋 SAMPLE DATA (First 10 rows):")
        print(df[['stock_symbol', 'company_name', 'type', 'author', 'created_utc', 'score']].head(10))
        print(f"\nColumns: {list(df.columns)}")
        
        # Show examples where stock was found in content
        content_matches = df[df['content'].notna() & (df['content'] != '')]
        if not content_matches.empty:
            print(f"\n✅ Found {len(content_matches)} messages with stock mentions in content")
            print("\nExample content snippets:")
            for idx, row in content_matches.head(3).iterrows():
                snippet = row['content'][:150] + "..." if len(row['content']) > 150 else row['content']
                print(f"\n  {row['stock_symbol']} - {snippet}")


if __name__ == "__main__":
    main()