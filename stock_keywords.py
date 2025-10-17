"""
Stock keywords database for Reddit AND Twitter scraping
Contains primary keywords (ticker symbols, company names) and context keywords (products, brands, CEOs)
"""

STOCK_KEYWORDS = {
    # French CAC 40 Stocks
    "AIR.PA": {
        "primary": ["AIR.PA", "AIR", "Airbus", "$AIR"],
        "context": ["A320", "A380", "A350", "aircraft", "aviation", "aerospace", 
                   "Boeing competitor", "European aircraft"],
        "company": "Airbus SE"
    },
    "BNP.PA": {
        "primary": ["BNP.PA", "BNP", "BNP Paribas", "$BNP", "Paribas"],
        "context": ["French bank", "European bank", "banking France", "Parisian bank"],
        "company": "BNP Paribas SA"
    },
    "SAN.PA": {
        "primary": ["SAN.PA", "SAN", "Sanofi", "$SAN"],
        "context": ["pharma", "pharmaceutical", "vaccine", "French pharma", 
                   "drug maker", "biotech France"],
        "company": "Sanofi SA"
    },
    "MC.PA": {
        "primary": ["MC.PA", "MC", "LVMH", "$MC", "Louis Vuitton", "Moët Hennessy"],
        "context": ["luxury", "Dior", "Fendi", "Givenchy", "Bernard Arnault", 
                   "luxury goods", "French luxury", "fashion house", "champagne"],
        "company": "LVMH Moët Hennessy Louis Vuitton SE"
    },
    "DG.PA": {
        "primary": ["DG.PA", "DG", "Vinci", "$DG", "Vinci SA"],
        "context": ["construction", "infrastructure", "French construction", 
                   "concessions", "contractor", "building"],
        "company": "Vinci SA"
    },
    "SU.PA": {
        "primary": ["SU.PA", "SU", "Schneider Electric", "Schneider", "$SU"],
        "context": ["electrical", "automation", "energy management", "industrial automation"],
        "company": "Schneider Electric SE"
    },
    "ENGI.PA": {
        "primary": ["ENGI.PA", "ENGI", "Engie", "$ENGI"],
        "context": ["energy", "utilities", "gas", "electricity", "renewable energy", 
                   "French utilities"],
        "company": "Engie SA"
    },
    "KER.PA": {
        "primary": ["KER.PA", "KER", "Kering", "$KER"],
        "context": ["Gucci", "Yves Saint Laurent", "YSL", "Balenciaga", 
                   "Bottega Veneta", "luxury fashion", "French luxury"],
        "company": "Kering SA"
    },
    
    # US Tech & Blue Chip Stocks
    "AAPL": {
        "primary": ["AAPL", "Apple", "$AAPL", "Apple Inc"],
        "context": ["iPhone", "iPad", "Mac", "MacBook", "Tim Cook", "iOS", 
                   "Apple Watch", "AirPods", "App Store", "iPod"],
        "company": "Apple Inc."
    },
    "MSFT": {
        "primary": ["MSFT", "Microsoft", "$MSFT", "MSFT stock"],
        "context": ["Windows", "Xbox", "Azure", "Office", "Teams", "LinkedIn", 
                   "Satya Nadella", "cloud computing", "Activision", "Surface"],
        "company": "Microsoft Corporation"
    },
    "GOOG": {
        "primary": ["GOOG", "GOOGL", "Google", "Alphabet", "$GOOG", "$GOOGL"],
        "context": ["search", "YouTube", "Android", "Chrome", "Pixel", "Waymo", 
                   "Google Cloud", "Sundar Pichai", "Gmail", "Google Maps"],
        "company": "Alphabet Inc. (Google)"
    },
    "AMZN": {
        "primary": ["AMZN", "Amazon", "$AMZN", "Amazon.com"],
        "context": ["AWS", "Prime", "e-commerce", "Alexa", "Whole Foods", 
                   "Jeff Bezos", "Andy Jassy", "Kindle", "Amazon Web Services"],
        "company": "Amazon.com Inc."
    },
    "META": {
        "primary": ["META", "Facebook", "$META", "Meta Platforms", "FB"],
        "context": ["Instagram", "WhatsApp", "Oculus", "metaverse", "Mark Zuckerberg", 
                   "Threads", "Reality Labs", "Quest", "VR"],
        "company": "Meta Platforms Inc."
    },
    "NVDA": {
        "primary": ["NVDA", "Nvidia", "NVIDIA", "$NVDA"],
        "context": ["GPU", "AI chips", "graphics card", "GeForce", "CUDA", 
                   "Jensen Huang", "RTX", "AI hardware", "datacenter", "gaming GPU"],
        "company": "NVIDIA Corporation"
    },
    "TSLA": {
        "primary": ["TSLA", "Tesla", "$TSLA", "Tesla Motors"],
        "context": ["Elon Musk", "electric vehicle", "EV", "Model 3", "Model Y", 
                   "Model S", "Cybertruck", "Autopilot", "FSD", "Supercharger", "Model X"],
        "company": "Tesla Inc."
    },
    "PEP": {
        "primary": ["PEP", "Pepsi", "PepsiCo", "$PEP"],
        "context": ["Pepsi Cola", "Frito-Lay", "Gatorade", "Quaker", "Tropicana", 
                   "Mountain Dew", "Doritos", "Lays", "beverage"],
        "company": "PepsiCo Inc."
    },
}

# Helper function to get all tickers
def get_all_tickers():
    """Return list of all stock tickers"""
    return list(STOCK_KEYWORDS.keys())

# Helper function to get stock info
def get_stock_info(ticker):
    """Get information for a specific ticker"""
    return STOCK_KEYWORDS.get(ticker, None)

# Helper function to add new stock
def add_stock(ticker, primary_keywords, context_keywords, company_name):
    """Add a new stock to the keywords database"""
    STOCK_KEYWORDS[ticker] = {
        "primary": primary_keywords,
        "context": context_keywords,
        "company": company_name
    }

def get_company_from_ticker(ticker):
    """Get company name from ticker symbol"""
    stock_info = STOCK_KEYWORDS.get(ticker, None)
    if stock_info:
        return stock_info["company"]
    return None