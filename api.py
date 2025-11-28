"""
Nigerian News API Gateway
FastAPI-based REST API for serving scraped tweets
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sqlite3
from datetime import datetime, timedelta
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Nigerian News API",
    description="REST API for accessing Nigerian news tweets",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class Tweet(BaseModel):
    id: int
    tweet_id: str
    author_username: str
    author_verified: bool
    account_category: str
    text: str
    created_at: str
    likes: int
    retweets: int
    replies: int
    url: str
    is_retweet: bool
    ingested_at: str
    processed: bool

class StatsResponse(BaseModel):
    total_tweets: int
    tweets_last_hour: int
    tweets_last_24h: int
    unique_authors: int
    categories: dict

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect("nigerian_news.db")
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Nigerian News API",
        "version": "1.0.0",
        "endpoints": {
            "/tweets": "Get all tweets with pagination and filters",
            "/tweets/top": "Get top trending tweets",
            "/tweets/recent": "Get most recent tweets",
            "/tweets/category/{category}": "Get tweets by category",
            "/stats": "Get API statistics",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tweets")
        count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_tweets": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get API statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Total tweets
        cursor.execute("SELECT COUNT(*) FROM tweets")
        total_tweets = cursor.fetchone()[0]
        
        # Tweets in last hour
        cursor.execute("""
            SELECT COUNT(*) FROM tweets 
            WHERE created_at > datetime('now', '-1 hour')
        """)
        tweets_last_hour = cursor.fetchone()[0]
        
        # Tweets in last 24 hours
        cursor.execute("""
            SELECT COUNT(*) FROM tweets 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        tweets_last_24h = cursor.fetchone()[0]
        
        # Unique authors
        cursor.execute("SELECT COUNT(DISTINCT author_username) FROM tweets")
        unique_authors = cursor.fetchone()[0]
        
        # Category breakdown
        cursor.execute("""
            SELECT account_category, COUNT(*) as count 
            FROM tweets 
            GROUP BY account_category
        """)
        categories = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return StatsResponse(
            total_tweets=total_tweets,
            tweets_last_hour=tweets_last_hour,
            tweets_last_24h=tweets_last_24h,
            unique_authors=unique_authors,
            categories=categories
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/tweets", response_model=List[Tweet])
async def get_tweets(
    limit: int = Query(50, ge=1, le=500, description="Number of tweets to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    min_engagement: Optional[int] = Query(None, ge=0, description="Minimum total engagement"),
    hours: Optional[int] = Query(None, ge=1, description="Only tweets from last N hours")
):
    """Get tweets with pagination and filters"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM tweets WHERE is_retweet = 0"
        params = []
        
        if category:
            query += " AND account_category = ?"
            params.append(category)
        
        if author:
            query += " AND author_username = ?"
            params.append(author)
        
        if hours:
            query += " AND created_at > datetime('now', ?)"
            params.append(f'-{hours} hours')
        
        if min_engagement:
            query += " AND (likes + retweets + replies) >= ?"
            params.append(min_engagement)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tweets = []
        for row in rows:
            tweets.append(Tweet(
                id=row['id'],
                tweet_id=row['tweet_id'],
                author_username=row['author_username'],
                author_verified=bool(row['author_verified']),
                account_category=row['account_category'],
                text=row['text'],
                created_at=row['created_at'],
                likes=row['likes'],
                retweets=row['retweets'],
                replies=row['replies'],
                url=row['url'],
                is_retweet=bool(row['is_retweet']),
                ingested_at=row['ingested_at'],
                processed=bool(row['processed'])
            ))
        
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tweets: {str(e)}")

@app.get("/tweets/top", response_model=List[Tweet])
async def get_top_tweets(
    limit: int = Query(20, ge=1, le=100, description="Number of top tweets to return"),
    hours: Optional[int] = Query(24, ge=1, description="Time window in hours")
):
    """Get top trending tweets by engagement"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM tweets 
            WHERE is_retweet = 0 
            AND created_at > datetime('now', ?)
            ORDER BY (likes + retweets + replies) DESC 
            LIMIT ?
        """
        
        cursor.execute(query, (f'-{hours} hours', limit))
        rows = cursor.fetchall()
        conn.close()
        
        tweets = []
        for row in rows:
            tweets.append(Tweet(
                id=row['id'],
                tweet_id=row['tweet_id'],
                author_username=row['author_username'],
                author_verified=bool(row['author_verified']),
                account_category=row['account_category'],
                text=row['text'],
                created_at=row['created_at'],
                likes=row['likes'],
                retweets=row['retweets'],
                replies=row['replies'],
                url=row['url'],
                is_retweet=bool(row['is_retweet']),
                ingested_at=row['ingested_at'],
                processed=bool(row['processed'])
            ))
        
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top tweets: {str(e)}")

@app.get("/tweets/recent", response_model=List[Tweet])
async def get_recent_tweets(
    limit: int = Query(50, ge=1, le=200, description="Number of recent tweets to return")
):
    """Get most recent tweets"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM tweets 
            WHERE is_retweet = 0 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        tweets = []
        for row in rows:
            tweets.append(Tweet(
                id=row['id'],
                tweet_id=row['tweet_id'],
                author_username=row['author_username'],
                author_verified=bool(row['author_verified']),
                account_category=row['account_category'],
                text=row['text'],
                created_at=row['created_at'],
                likes=row['likes'],
                retweets=row['retweets'],
                replies=row['replies'],
                url=row['url'],
                is_retweet=bool(row['is_retweet']),
                ingested_at=row['ingested_at'],
                processed=bool(row['processed'])
            ))
        
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent tweets: {str(e)}")

@app.get("/tweets/category/{category}", response_model=List[Tweet])
async def get_tweets_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=200, description="Number of tweets to return")
):
    """Get tweets by category"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM tweets 
            WHERE account_category = ? AND is_retweet = 0 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        
        cursor.execute(query, (category, limit))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No tweets found for category: {category}")
        
        tweets = []
        for row in rows:
            tweets.append(Tweet(
                id=row['id'],
                tweet_id=row['tweet_id'],
                author_username=row['author_username'],
                author_verified=bool(row['author_verified']),
                account_category=row['account_category'],
                text=row['text'],
                created_at=row['created_at'],
                likes=row['likes'],
                retweets=row['retweets'],
                replies=row['replies'],
                url=row['url'],
                is_retweet=bool(row['is_retweet']),
                ingested_at=row['ingested_at'],
                processed=bool(row['processed'])
            ))
        
        return tweets
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tweets: {str(e)}")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
