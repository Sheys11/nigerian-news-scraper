import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize SQLite database with production schema"""
    conn = sqlite3.connect("nigerian_news.db")
    cursor = conn.cursor()
    
    # Create main tweets table
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
    
    # Migration: Add new columns if they don't exist
    try:
        cursor.execute("ALTER TABLE tweets ADD COLUMN author_verified BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE tweets ADD COLUMN ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE tweets ADD COLUMN processed BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    return conn

def store_tweets(conn, tweets: list):
    """Store tweets in SQLite database"""
    cursor = conn.cursor()
    stored_count = 0
    
    for tweet in tweets:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO tweets (
                    tweet_id, author_username, author_verified, account_category,
                    text, created_at, likes, retweets, replies,
                    url, is_retweet, ingested_at, processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, FALSE)
            """, (
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
                tweet["is_retweet"]
            ))
            stored_count += 1
            print(f"Successfully stored tweet {tweet['tweet_id']}")
        except Exception as e:
            logger.error(f"Error storing tweet {tweet['tweet_id']}: {e}")
    
    conn.commit()
    logger.info(f"✓ Stored {stored_count} tweets in database")

if __name__ == "__main__":
    print("Initializing DB...")
    conn = init_database()
    
    print("Attempting to store dummy tweet...")
    dummy_tweet = {
        "tweet_id": "debug_12345",
        "author_username": "debug_user",
        "author_verified": True,
        "category": "debug",
        "text": "This is a debug tweet",
        "created_at": datetime.now().isoformat(),
        "likes": 10,
        "retweets": 5,
        "replies": 2,
        "url": "https://x.com/debug_user/status/debug_12345",
        "is_retweet": False
    }
    
    store_tweets(conn, [dummy_tweet])
    
    # Verify insertion
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tweets WHERE tweet_id = 'debug_12345'")
    row = cursor.fetchone()
    if row:
        print("Verification successful: Tweet found in DB")
        print(row)
    else:
        print("Verification failed: Tweet not found in DB")
    
    conn.close()
