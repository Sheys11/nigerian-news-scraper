"""
Nigerian News Twitter Scraper using Playwright - Production Version
Scrapes tweets from X (Twitter) without API requirements
Features: Exponential backoff, 60-min time filter, enhanced schema
"""

import asyncio
from playwright.async_api import async_playwright, Page
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
import logging
import random
import re
import os
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"scraper_{datetime.now().strftime('%Y-%m-%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# 1. CONFIGURATION & CONSTANTS
# ============================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

TIME_WINDOW_MINUTES = 60  # Only scrape tweets from last 60 minutes

ACCOUNTS = {
    "news_outlets": [
        "channelstv", "guardian", "PremiumTimesNG", "SaharaReporters", "TheCablNG",
        "LegitNG", "DailyPostNGR", "thenationonline", "NgNewsAgency", "dailytrust",
        "BunchNews", "pointblanknewsnigeria", "informationng",
    ],
    "journalists": [
        "DavidHundeyin", "ToluOgunlesi", "ZainabUsman", "Chidinmaiwueze",
        "irenecnwoye", "OseniRufai", "KemiOlunloyo", "Omojuwa",
    ],
    "activists": [
        "AishaYesufu", "RinuOduala", "Letter_to_Jack", "falzthebadhguy",
        "DJ_Switch_", "MaziIbe",
    ],
    "grassroots": [
        "Adenike_Oladosu", "TreeWithTunde", "ChidiOdinkalu", "AyoSogunro",
        "DrJoeAbah", "Ikeoluwa", "PeaceItimi", "Nenne_Adora", "Bolarinwa_Debo",
        "FisayoFosudo", "TosinOlaseinde", "NaijaFlyingDr", "Aunty_Ada", "OneJoblessBoy",
    ],
    "commentary": [
        "Mr_Macaroni", "LayiWasabi", "KusssmanTV", "arojinle1",
        "Morris_Monye", "Wizarab", "Ebuka_Obi_Uchendu",
    ],
}

# ============================================================================
# 2. DATABASE SETUP
# ============================================================================

def get_db_connection():
    """Get database connection from DATABASE_URL"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback to local SQLite for development if no URL provided
        logger.warning("DATABASE_URL not set, falling back to SQLite 'nigerian_news.db'")
        import sqlite3
        return sqlite3.connect("nigerian_news.db")
    return psycopg2.connect(db_url)

def init_database():
    """Initialize database with production schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we are using SQLite or Postgres
    is_sqlite = hasattr(conn, 'execute') and not hasattr(conn, 'status') # Rough check
    
    if is_sqlite:
        # SQLite Schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id TEXT UNIQUE NOT NULL,
                author_username TEXT NOT NULL,
                author_verified BOOLEAN DEFAULT FALSE,
                account_category TEXT,
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                likes INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                url TEXT,
                is_retweet BOOLEAN DEFAULT FALSE,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)
    else:
        # PostgreSQL Schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id SERIAL PRIMARY KEY,
                tweet_id TEXT UNIQUE NOT NULL,
                author_username TEXT NOT NULL,
                author_verified BOOLEAN DEFAULT FALSE,
                account_category TEXT,
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                likes INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                url TEXT,
                is_retweet BOOLEAN DEFAULT FALSE,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)
    
    
    conn.commit()
    
    # Create indexes
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON tweets(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweet_id ON tweets(tweet_id)")
    except Exception as e:
        logger.warning(f"Error creating indexes: {e}")
    
    # Migration: Add new columns if they don't exist
    columns_to_add = [
        ("author_verified", "BOOLEAN DEFAULT FALSE"),
        ("ingested_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("processed", "BOOLEAN DEFAULT FALSE")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            if is_sqlite:
                cursor.execute(f"ALTER TABLE tweets ADD COLUMN {col_name} {col_type}")
            else:
                cursor.execute(f"ALTER TABLE tweets ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
        except Exception:
            pass # Column likely exists (SQLite throws error if exists)
            
    conn.commit()
    return conn

def get_placeholder(conn):
    """Return SQL placeholder based on connection type"""
    # Check if SQLite (has execute but no status)
    if hasattr(conn, 'execute') and not hasattr(conn, 'status'):
        return "?"
    return "%s"
    logger.info("Database initialized successfully")
    return conn

def check_tweet_exists(conn, tweet_id):
    """Check if tweet already exists in database"""
    cursor = conn.cursor()
    ph = get_placeholder(conn)
    cursor.execute(f"SELECT 1 FROM tweets WHERE tweet_id = {ph}", (tweet_id,))
    return cursor.fetchone() is not None

# ============================================================================
# 3. UTILITIES
# ============================================================================

def parse_relative_time(time_str):
    """Parse Twitter's relative time strings into ISO format"""
    now = datetime.now()
    
    try:
        if not time_str:
            return now.isoformat()
            
        # Handle "23s", "45m", "2h"
        if time_str.endswith('s'):
            seconds = int(time_str[:-1])
            return (now - timedelta(seconds=seconds)).isoformat()
        elif time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return (now - timedelta(minutes=minutes)).isoformat()
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            return (now - timedelta(hours=hours)).isoformat()
            
        # Handle "Jan 1" (current year)
        try:
            dt = datetime.strptime(f"{time_str} {now.year}", "%b %d %Y")
            if dt > now:  # Must be previous year
                dt = dt.replace(year=now.year - 1)
            return dt.isoformat()
        except ValueError:
            pass
            
        # Handle "Dec 31, 2023"
        try:
            dt = datetime.strptime(time_str, "%b %d, %Y")
            return dt.isoformat()
        except ValueError:
            pass
            
        return now.isoformat()
        
    except Exception as e:
        logger.warning(f"Error parsing time '{time_str}': {e}")
        return now.isoformat()

def is_within_time_window(timestamp_str, window_minutes=TIME_WINDOW_MINUTES):
    """Check if timestamp is within the specified time window"""
    try:
        tweet_time = datetime.fromisoformat(timestamp_str)
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        return tweet_time >= cutoff_time
    except Exception as e:
        logger.warning(f"Error checking time window for '{timestamp_str}': {e}")
        return False

# ============================================================================
# 4. PLAYWRIGHT SCRAPING
# ============================================================================

async def scrape_account_tweets(page: Page, username: str, category: str, conn, max_tweets: int = 50) -> list:
    """Scrape recent tweets from a single X account using Playwright"""
    tweets = []
    url = f"https://x.com/{username}"
    
    try:
        logger.info(f"Navigating to @{username}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for tweets to load
        try:
            await page.wait_for_selector('article', timeout=15000)
        except Exception:
            logger.warning(f"Timeout waiting for articles on @{username}")
            return tweets
        
        # Scroll to load more tweets
        previous_height = 0
        tweets_loaded = 0
        consecutive_duplicates = 0
        old_tweets_count = 0
        
        while tweets_loaded < max_tweets and old_tweets_count < 10:
            # Get all tweet articles
            articles = await page.query_selector_all('article')
            logger.info(f"  Loaded {len(articles)} articles, extracting...")
            
            for article in articles:
                if tweets_loaded >= max_tweets:
                    break
                
                try:
                    # Extract tweet text
                    text_elem = await article.query_selector('[data-testid="tweetText"]')
                    if not text_elem:
                        continue
                    
                    tweet_text = await text_elem.inner_text()
                    
                    # Extract metrics (likes, retweets, replies)
                    metrics = await article.query_selector_all('[role="button"]')
                    likes = retweets = replies = 0
                    
                    for metric in metrics:
                        try:
                            text = await metric.inner_text()
                            if "Like" in text or "❤️" in text:
                                likes = int(text.split()[0]) if text[0].isdigit() else 0
                            elif "Repost" in text:
                                retweets = int(text.split()[0]) if text[0].isdigit() else 0
                            elif "Reply" in text:
                                replies = int(text.split()[0]) if text[0].isdigit() else 0
                        except:
                            pass
                    
                    # Extract tweet link and time
                    link_elem = await article.query_selector('a[href*="/status/"]')
                    time_elem = await article.query_selector('time')
                    
                    tweet_url = await link_elem.get_attribute('href') if link_elem else ""
                    time_str = await time_elem.inner_text() if time_elem else ""
                    
                    # Create tweet ID from URL
                    tweet_id = tweet_url.split('/status/')[-1].split('?')[0] if '/status/' in tweet_url else ""
                    
                    if tweet_id and tweet_text:
                        # Parse timestamp
                        created_at = parse_relative_time(time_str)
                        
                        # Check if tweet is within time window (60 minutes)
                        if not is_within_time_window(created_at):
                            old_tweets_count += 1
                            logger.debug(f"Skipping old tweet from @{username}: {time_str}")
                            continue
                        
                        # Incremental check
                        if check_tweet_exists(conn, tweet_id):
                            consecutive_duplicates += 1
                            if consecutive_duplicates >= 5:
                                logger.info(f"  Found 5 duplicates in a row. Stopping scrape for @{username}.")
                                return tweets
                            continue
                        
                        consecutive_duplicates = 0  # Reset if we find a new tweet
                        
                        # Extract author verification status
                        verified_badge = await article.query_selector('[data-testid="icon-verified"]')
                        is_verified = verified_badge is not None
                        
                        tweets.append({
                            "tweet_id": tweet_id,
                            "author_username": username,
                            "author_verified": is_verified,
                            "category": category,
                            "text": tweet_text,
                            "likes": likes,
                            "retweets": retweets,
                            "replies": replies,
                            "url": f"https://x.com{tweet_url}" if tweet_url else "",
                            "is_retweet": tweet_text.startswith("RT @"),
                            "created_at": created_at,
                        })
                        tweets_loaded += 1
                
                except Exception as e:
                    logger.warning(f"Error extracting tweet: {e}")
                    continue
            
            # Stop if we've seen too many old tweets
            if old_tweets_count >= 10:
                logger.info(f"  Found 10 tweets older than {TIME_WINDOW_MINUTES} minutes. Stopping scrape for @{username}.")
                break
            
            # Scroll down to load more
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                logger.info(f"  Reached end of feed for @{username}")
                break
            
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            previous_height = new_height
            
            # Wait for new content to load
            await asyncio.sleep(2)
        
        logger.info(f"✓ Scraped {len(tweets)} tweets from @{username}")
        return tweets
    
    except Exception as e:
        logger.error(f"Error scraping @{username}: {e}")
        return tweets

async def scrape_all_accounts(accounts_dict: dict, conn) -> list:
    """Scrape all tracked accounts with exponential backoff retry logic"""
    all_tweets = []
    failure_tracker = {}
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        
        for category, usernames in accounts_dict.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Scraping {category}...")
            logger.info(f"{'='*60}")
            
            for username in usernames:
                # Exponential backoff retry logic
                max_retries = 3
                base_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        # Rotate User-Agent
                        user_agent = random.choice(USER_AGENTS)
                        context = await browser.new_context(user_agent=user_agent)
                        page = await context.new_page()
                        
                        tweets = await scrape_account_tweets(page, username, category, conn, max_tweets=50)
                        all_tweets.extend(tweets)
                        
                        await context.close()
                        
                        # Reset failure tracker on success
                        failure_tracker[username] = 0
                        break
                        
                    except Exception as e:
                        logger.warning(f"Attempt {attempt+1}/{max_retries} failed for @{username}: {e}")
                        
                        # Track consecutive failures
                        failure_tracker[username] = failure_tracker.get(username, 0) + 1
                        
                        if attempt < max_retries - 1:
                            # Exponential backoff: 1s, 2s, 4s
                            delay = base_delay * (2 ** attempt)
                            logger.info(f"Waiting {delay}s before retry...")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"Failed to scrape @{username} after {max_retries} attempts")
                            
                            # Alert if consecutive failures > 3
                            if failure_tracker[username] > 3:
                                logger.critical(f"ALERT: @{username} has failed {failure_tracker[username]} consecutive times!")
                
                # Be respectful to the server - wait between requests
                await asyncio.sleep(3)
        
        await browser.close()
    
    return all_tweets

# ============================================================================
# 5. FILTER & QUALITY CONTROL
# ============================================================================

def apply_quality_filters(tweets: list, min_engagement: int = 30) -> list:
    """Filter tweets based on quality metrics"""
    filtered = []
    
    for tweet in tweets:
        # Skip retweets
        if tweet["is_retweet"]:
            continue
        
        # Min engagement threshold
        total_engagement = tweet["likes"] + tweet["retweets"] + tweet["replies"]
        if total_engagement < min_engagement:
            continue
        
        # Skip very short tweets
        if len(tweet["text"]) < 50:
            continue
        
        filtered.append(tweet)
    
    return filtered

def detect_news_relevance(tweet_text: str) -> int:
    """Score tweet for news relevance"""
    keywords = [
        "breaking", "urgent", "news", "confirmed",
        "government", "president", "minister", "parliament",
        "security", "protest", "strike", "arrested",
        "economy", "inflation", "business", "deal",
        "health", "hospital", "disease", "outbreak",
        "election", "vote", "campaign", "politics",
        "corruption", "accountability", "justice"
    ]
    
    relevance_score = 0
    text_lower = tweet_text.lower()
    
    for keyword in keywords:
        if keyword in text_lower:
            relevance_score += 1
    
    return relevance_score

def enrich_tweets(tweets: list) -> list:
    """Add metadata and relevance scores"""
    for tweet in tweets:
        tweet["relevance_score"] = detect_news_relevance(tweet["text"])
    
    return tweets

# ============================================================================
# 6. STORE IN DATABASE
# ============================================================================

def store_tweets(conn, tweets: list):
    """Store tweets in database"""
    cursor = conn.cursor()
    stored_count = 0
    ph = get_placeholder(conn)
    is_sqlite = ph == "?"
    
    for tweet in tweets:
        try:
            if is_sqlite:
                query = f"""
                    INSERT OR REPLACE INTO tweets (
                        tweet_id, author_username, author_verified, account_category,
                        text, created_at, likes, retweets, replies,
                        url, is_retweet, ingested_at, processed
                    ) VALUES ({', '.join([ph]*13)})
                """
            else:
                query = f"""
                    INSERT INTO tweets (
                        tweet_id, author_username, author_verified, account_category,
                        text, created_at, likes, retweets, replies,
                        url, is_retweet, ingested_at, processed
                    ) VALUES ({', '.join([ph]*13)})
                    ON CONFLICT (tweet_id) DO UPDATE SET
                        likes = EXCLUDED.likes,
                        retweets = EXCLUDED.retweets,
                        replies = EXCLUDED.replies,
                        processed = FALSE
                """
                
            cursor.execute(query, (
                tweet["tweet_id"],
                tweet["author_username"],
                tweet.get("author_verified", False),
                tweet["category"],
                tweet["text"],
                tweet["created_at"],
                tweet["likes"],
                tweet["retweets"],
                tweet["replies"],
                tweet["url"],
                tweet["is_retweet"],
                datetime.now(), # ingested_at
                False # processed
            ))
            stored_count += 1
        except Exception as e:
            logger.error(f"Error storing tweet {tweet['tweet_id']}: {e}")
            # If Postgres transaction fails, we might need to rollback
            if not is_sqlite:
                conn.rollback()
    
    conn.commit()
    logger.info(f"✓ Stored {stored_count} tweets in database")

# ============================================================================
# 7. QUERY & EXPORT RESULTS
# ============================================================================

def get_top_stories(conn, limit: int = 20) -> list:
    """Retrieve top stories from database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT author_username, text, likes, retweets, replies, url, account_category
        FROM tweets
        WHERE is_retweet = 0
        ORDER BY (likes + retweets + replies) DESC
        LIMIT ?
    """, (limit,))
    
    return cursor.fetchall()

def export_to_json(conn, filename: str = "nigerian_news.json"):
    """Export tweets to JSON file"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM tweets
        WHERE is_retweet = 0
        ORDER BY created_at DESC
        LIMIT 500
    """)
    
    columns = [desc[0] for desc in cursor.description]
    results = cursor.fetchall()
    
    tweets_list = [dict(zip(columns, row)) for row in results]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(tweets_list, f, indent=2, default=str)
    
    logger.info(f"✓ Exported {len(tweets_list)} tweets to {filename}")

# ============================================================================
# 8. MAIN EXECUTION
# ============================================================================

async def main():
    """Main scraper workflow"""
    logger.info("🚀 Starting Nigerian News Scraper (Production)...")
    logger.info(f"Time window: Last {TIME_WINDOW_MINUTES} minutes")
    
    # Initialize database
    conn = init_database()
    
    try:
        # Step 1: Scrape all accounts
        logger.info("\n📡 Step 1: Scraping tweets from all accounts...")
        all_tweets = await scrape_all_accounts(ACCOUNTS, conn)
        logger.info(f"✓ Fetched {len(all_tweets)} raw tweets")
        
        # Step 2: Apply quality filters
        logger.info("\n🔍 Step 2: Applying quality filters...")
        filtered_tweets = apply_quality_filters(all_tweets, min_engagement=30)
        logger.info(f"✓ Filtered to {len(filtered_tweets)} high-quality tweets")
        
        # Step 3: Enrich with metadata
        logger.info("\n🏷️ Step 3: Enriching tweets with metadata...")
        enriched_tweets = enrich_tweets(filtered_tweets)
        
        # Step 4: Store in database
        logger.info("\n💾 Step 4: Storing tweets in database...")
        store_tweets(conn, enriched_tweets)
        
        # Step 5: Display results
        logger.info("\n" + "="*80)
        logger.info("TOP 15 TRENDING STORIES")
        logger.info("="*80)
        
        top_stories = get_top_stories(conn, limit=15)
        
        for i, story in enumerate(top_stories, 1):
            username, text, likes, retweets, replies, url, category = story
            total_engagement = likes + retweets + replies
            print(f"\n{i}. @{username} [{category}]")
            print(f"   {text[:120]}...")
            print(f"   ❤️ {likes} | 🔄 {retweets} | 💬 {replies} (Total: {total_engagement})")
        
        # Step 6: Export to JSON
        logger.info("\n📁 Step 6: Exporting to JSON...")
        export_to_json(conn)
        
        logger.info("\n✅ Scraper completed successfully!")
    
    except Exception as e:
        logger.critical(f"Fatal error in main workflow: {e}", exc_info=True)
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(main())
