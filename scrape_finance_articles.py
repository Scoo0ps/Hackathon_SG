from time import sleep
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import numpy as np
import time
from random import uniform
from stock_keywords import STOCK_KEYWORDS, get_company_from_ticker
from datetime import datetime, timedelta
import re
import pandas as pd


def convert_timestamp(timestamp_str):
    """Convert timestamp from 'h hr ago' format or date format to actual date"""
    if not timestamp_str:
        return None
    
    # Check for "h hr ago" or "hh hr ago" pattern
    match = re.match(r'(\d+)\s+hr\s+ago', timestamp_str.strip())
    if match:
        hours_ago = int(match.group(1))
        current_time = datetime.now()
        actual_time = current_time - timedelta(hours=hours_ago)
        return actual_time.strftime('%Y-%m-%d')
    
    # Try to parse date formats like "October 15, 2025"
    try:
        parsed_date = datetime.strptime(timestamp_str.strip(), '%B %d, %Y')
        return parsed_date.strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try other common date formats
    date_formats = [
        '%Y-%m-%d',  # Already in correct format
        '%m/%d/%Y',  # MM/DD/YYYY
        '%d/%m/%Y',  # DD/MM/YYYY
        '%Y-%m-%d %H:%M:%S'  # Format with time
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(timestamp_str.strip(), fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If not in any recognized format, return as is
    return timestamp_str

def scrape_bloomberg(playwright, company):
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="chrome_cache",
        accept_downloads=True,
        headless=False,
        bypass_csp=True,
        slow_mo=100,
        channel="chrome",
        args=['--disable-blink-features=AutomationControlled']
    )

    page = browser.new_page()
    all_articles = []  # List to store all articles for DataFrame

    print(f"Scraping {company} on Bloomberg...\n\n")
    page.goto(f"https://www.bloomberg.com/search?query={company}&sort=relevance&start_time=-1m")

    for i in range(3):
        load_more_button = page.locator('//button[contains(@class, "LoadMoreButton")]')
        load_more_button.click()
        sleep(3)

    # Get page source and parse with Beautiful Soup
    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    containers = soup.find_all('div', class_=lambda c: c and 'SearchResult_rowOrStackResultTimestamp' in c)

    # Create list to store article objects
    articles_data = []
    
    for container in containers:
        summary_section = container.find('section', {'data-component': 'summary'})
        time_tag = container.find('time', class_=lambda c: c and 'SearchResult_itemTimestamp' in c)
        timestamp = time_tag.text.strip() if time_tag else None
        
        # Convert timestamp if in "hr ago" format
        converted_timestamp = convert_timestamp(timestamp)
        
        if summary_section:
            article_obj = {
                'summary': summary_section.get_text().strip(),
                'timestamp': converted_timestamp,
                'element': summary_section
            }
            articles_data.append(article_obj)

    # Track unique texts to avoid duplicates
    unique_texts = []
    filtered_articles = []

    # Apply filtering logic
    for article in articles_data:
        section_text = article['summary'].lower()
        
        # Check if contains company name
        company_found = company.lower() in section_text
        
        # Check if contains any stock keywords
        context_found = any(keyword.lower() in section_text for keyword in STOCK_KEYWORDS)
        
        # Only include if either company OR context are found, and text is not duplicate
        if (company_found or context_found) and section_text not in unique_texts:
            unique_texts.append(section_text)
            filtered_articles.append(article)
            print(f"{company}-Article matches company or context criteria")
        else:
            if not company_found and not context_found:
                print(f"{company}-Removed: Neither company name nor stock keywords found in article")
            else:
                print(f"{company}-Removed: Duplicate article")
            print("--------------\n")
            
    if filtered_articles:
        print(f"{company}-Summary section(s) found\n")
        for article in filtered_articles:
            print(f"Timestamp: {article['timestamp']}")
            print(f"Summary: {article['summary']}\n")
            
            # Add to all_articles list for DataFrame
            all_articles.append({
                'company_name': company,
                'content': article['summary'],
                'created_utc': article['timestamp'],
                'source': 'bloomberg'
            })
            print("--------------\n")
    else:
        print(f"{company}-No relevant summary sections found \n")

    time.sleep(uniform(1, 1.5))
    
    browser.close()
    
    # Create and return DataFrame
    df = pd.DataFrame(all_articles)
    return df


if __name__ == "__main__":
    company = "Apple"
    
    with sync_playwright() as playwright:
        articles_df = scrape_bloomberg(playwright, company)
    
    print(articles_df)

    