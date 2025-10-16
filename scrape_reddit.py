import praw
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import time

# Load environment variables
load_dotenv()

class RedditStockScraper:
    def __init__(self):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'StockScraper/1.0')
        )
        
        # Stock symbols to search for
        self.stock_symbols = ['AAPL', 'LVMH', 'GOOGL', 'MSFT', 'MICROSOFT']
        
        # Financial subreddits to scrape
        self.financial_subreddits = [
            'investing',
            'stocks',
            'SecurityAnalysis',
            'ValueInvesting',
            'financialindependence',
            'StockMarket',
            'pennystocks',
            'wallstreetbets',
            'SecurityAnalysis',
            'finance'
        ]
        
        self.scraped_data = []
    
    def is_stock_related(self, text, symbol):
        """Check if text contains mentions of the stock symbol"""
        # Create pattern to match stock symbol (case insensitive)
        patterns = [
            rf'\b{symbol}\b',  # Exact match
            rf'\${symbol}\b',  # With $ prefix
            rf'{symbol.lower()}\b',  # Lowercase
        ]
        
        # Special case for Microsoft
        if symbol == 'MSFT':
            patterns.extend([r'\bmicrosoft\b', r'\bMicrosoft\b', r'\bMICROSOFT\b'])
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def scrape_subreddit(self, subreddit_name, limit=100, time_filter='week'):
        """Scrape a specific subreddit for stock-related posts and comments"""
        print(f"Scraping r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get hot posts
            for submission in subreddit.hot(limit=limit):
                self.process_submission(submission)
                
            # Get new posts
            for submission in subreddit.new(limit=limit):
                self.process_submission(submission)
                
        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {str(e)}")
    
    def process_submission(self, submission):
        """Process a Reddit submission (post) and its comments"""
        # Check if post title or text mentions any stock
        for symbol in self.stock_symbols:
            if (self.is_stock_related(submission.title, symbol) or 
                self.is_stock_related(submission.selftext, symbol)):
                
                # Add post data
                self.scraped_data.append({
                    'type': 'post',
                    'subreddit': submission.subreddit.display_name,
                    'stock_symbol': symbol,
                    'id': submission.id,
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
                self.process_comments(submission, symbol)
                break  # Avoid duplicate entries for posts mentioning multiple stocks
    
    def process_comments(self, submission, symbol):
        """Process comments from a submission"""
        try:
            submission.comments.replace_more(limit=0)  # Remove "more comments" objects
            
            for comment in submission.comments.list():
                if hasattr(comment, 'body') and self.is_stock_related(comment.body, symbol):
                    self.scraped_data.append({
                        'type': 'comment',
                        'subreddit': submission.subreddit.display_name,
                        'stock_symbol': symbol,
                        'id': comment.id,
                        'title': submission.title,  # Parent post title
                        'content': comment.body,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'score': comment.score,
                        'upvote_ratio': None,  # Comments don't have upvote ratio
                        'num_comments': None,
                        'created_utc': datetime.fromtimestamp(comment.created_utc),
                        'url': submission.url,
                        'permalink': f"https://reddit.com{comment.permalink}"
                    })
        except Exception as e:
            print(f"Error processing comments: {str(e)}")
    
    def scrape_all_subreddits(self, limit_per_sub=50):
        """Scrape all financial subreddits"""
        print("Starting Reddit scraping for stock discussions...")
        
        for subreddit in self.financial_subreddits:
            self.scrape_subreddit(subreddit, limit=limit_per_sub)
            time.sleep(1)  # Be respectful to Reddit's API
        
        print(f"Scraping completed. Found {len(self.scraped_data)} relevant posts/comments.")
    
    def save_to_csv(self, filename=None):
        """Save scraped data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_stock_data_{timestamp}.csv"
        
        if self.scraped_data:
            df = pd.DataFrame(self.scraped_data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save.")
            return None
    
    def get_summary(self):
        """Get summary statistics of scraped data"""
        if not self.scraped_data:
            return "No data scraped yet."
        
        df = pd.DataFrame(self.scraped_data)
        
        summary = {
            'total_items': len(df),
            'posts': len(df[df['type'] == 'post']),
            'comments': len(df[df['type'] == 'comment']),
            'by_stock': df['stock_symbol'].value_counts().to_dict(),
            'by_subreddit': df['subreddit'].value_counts().to_dict(),
            'date_range': f"{df['created_utc'].min()} to {df['created_utc'].max()}"
        }
        
        return summary

def main():
    """Main function to run the scraper"""
    # Create scraper instance
    scraper = RedditStockScraper()
    
    # Scrape data
    scraper.scrape_all_subreddits(limit_per_sub=200)
    
    # Save to CSV
    df = scraper.save_to_csv()
    
    # Print summary
    summary = scraper.get_summary()
    print("\n=== SCRAPING SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print(df["content"])

if __name__ == "__main__":
    main()