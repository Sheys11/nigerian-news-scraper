import aiosqlite
import json
import logging
from datetime import datetime
from .config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the SQLite database with required tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                tweet_id TEXT PRIMARY KEY,
                author_username TEXT,
                category TEXT,
                text TEXT,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                total_engagement INTEGER,
                url TEXT,
                timestamp DATETIME,
                relevance_score INTEGER,
                collected_at DATETIME
            )
        """)
        await db.commit()
        logger.info(f"Database initialized at {DB_PATH}")

async def save_tweet(tweet_data):
    """Save a single tweet to the database"""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("""
                INSERT OR REPLACE INTO tweets (
                    tweet_id, author_username, category, text,
                    likes, retweets, replies, total_engagement,
                    url, timestamp, relevance_score, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tweet_data['tweet_id'],
                tweet_data['author_username'],
                tweet_data['category'],
                tweet_data['text'],
                tweet_data['likes'],
                tweet_data['retweets'],
                tweet_data['replies'],
                tweet_data['total_engagement'],
                tweet_data['url'],
                tweet_data['timestamp'],
                tweet_data['relevance_score'],
                datetime.now().isoformat()
            ))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving tweet {tweet_data.get('tweet_id')}: {e}")
            return False

async def get_top_stories(limit=15):
    """Retrieve top stories sorted by engagement"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM tweets 
            ORDER BY total_engagement DESC 
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_tweets_for_export(limit=500):
    """Retrieve recent tweets for JSON export"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM tweets 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
