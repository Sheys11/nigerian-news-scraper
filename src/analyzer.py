import logging
from .config import KEYWORDS, MIN_ENGAGEMENT

logger = logging.getLogger(__name__)

def calculate_relevance_score(text):
    """Calculate relevance score based on keywords"""
    score = 0
    text_lower = text.lower()
    
    # Base score for being from a tracked account
    score += 1
    
    # Keyword scoring
    for keyword in KEYWORDS:
        if keyword in text_lower:
            # Higher weight for urgent keywords
            if keyword in ["breaking", "urgent", "confirmed"]:
                score += 5
            elif keyword in ["security", "government", "economy"]:
                score += 3
            else:
                score += 1
                
    return score

def parse_metric(metric_str):
    """Parse metric string (e.g., '1.2K', '500') to integer"""
    if not metric_str:
        return 0
        
    metric_str = metric_str.strip().upper()
    multiplier = 1
    
    if metric_str.endswith('K'):
        multiplier = 1000
        metric_str = metric_str[:-1]
    elif metric_str.endswith('M'):
        multiplier = 1000000
        metric_str = metric_str[:-1]
    elif metric_str.endswith('B'):
        multiplier = 1000000000
        metric_str = metric_str[:-1]
        
    try:
        return int(float(metric_str) * multiplier)
    except ValueError:
        return 0

def filter_tweet(tweet_data):
    """
    Filter tweet based on quality criteria.
    Returns True if tweet should be kept, False otherwise.
    """
    # Skip retweets (usually start with RT @)
    if tweet_data['text'].startswith("RT @"):
        return False
        
    # Skip short tweets
    if len(tweet_data['text']) < 20:
        return False
        
    # Check engagement
    if tweet_data['total_engagement'] < MIN_ENGAGEMENT:
        return False
        
    return True
