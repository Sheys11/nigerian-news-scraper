# API Gateway Documentation

## Overview
The Nigerian News API provides RESTful endpoints for accessing scraped tweets from Nigerian news sources.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required (add API keys in production).

## Endpoints

### GET /
Root endpoint with API information.

**Response:**
```json
{
  "message": "Nigerian News API",
  "version": "1.0.0",
  "endpoints": {...}
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "total_tweets": 1234,
  "timestamp": "2025-11-28T05:00:00"
}
```

### GET /stats
Get API statistics.

**Response:**
```json
{
  "total_tweets": 1234,
  "tweets_last_hour": 45,
  "tweets_last_24h": 567,
  "unique_authors": 48,
  "categories": {
    "news_outlets": 500,
    "journalists": 300,
    ...
  }
}
```

### GET /tweets
Get tweets with pagination and filters.

**Query Parameters:**
- `limit` (int, default=50, max=500): Number of tweets to return
- `offset` (int, default=0): Offset for pagination
- `category` (string, optional): Filter by category
- `author` (string, optional): Filter by author username
- `min_engagement` (int, optional): Minimum total engagement
- `hours` (int, optional): Only tweets from last N hours

**Example:**
```
GET /tweets?limit=20&category=news_outlets&hours=24
```

**Response:**
```json
[
  {
    "id": 1,
    "tweet_id": "1234567890",
    "author_username": "channelstv",
    "author_verified": true,
    "account_category": "news_outlets",
    "text": "Breaking news...",
    "created_at": "2025-11-28T04:30:00",
    "likes": 150,
    "retweets": 45,
    "replies": 12,
    "url": "https://x.com/channelstv/status/1234567890",
    "is_retweet": false,
    "ingested_at": "2025-11-28T04:35:00",
    "processed": false
  }
]
```

### GET /tweets/top
Get top trending tweets by engagement.

**Query Parameters:**
- `limit` (int, default=20, max=100): Number of top tweets
- `hours` (int, default=24): Time window in hours

**Example:**
```
GET /tweets/top?limit=10&hours=12
```

### GET /tweets/recent
Get most recent tweets.

**Query Parameters:**
- `limit` (int, default=50, max=200): Number of recent tweets

**Example:**
```
GET /tweets/recent?limit=30
```

### GET /tweets/category/{category}
Get tweets by category.

**Path Parameters:**
- `category` (string): Category name (news_outlets, journalists, activists, grassroots, commentary)

**Query Parameters:**
- `limit` (int, default=50, max=200): Number of tweets

**Example:**
```
GET /tweets/category/journalists?limit=25
```

## Running the API

### Development
```bash
source .venv/bin/activate
pip install -r requirements.txt
python api.py
```

The API will be available at `http://localhost:8000`.

### Production (with Uvicorn)
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Interactive Documentation
FastAPI provides automatic interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

### Python
```python
import requests

# Get top tweets
response = requests.get("http://localhost:8000/tweets/top?limit=10")
tweets = response.json()

for tweet in tweets:
    print(f"@{tweet['author_username']}: {tweet['text'][:50]}...")
```

### cURL
```bash
# Get recent tweets
curl "http://localhost:8000/tweets/recent?limit=20"

# Get tweets by category
curl "http://localhost:8000/tweets/category/news_outlets"

# Get stats
curl "http://localhost:8000/stats"
```

### JavaScript/Fetch
```javascript
// Get top trending tweets
fetch('http://localhost:8000/tweets/top?limit=15')
  .then(response => response.json())
  .then(tweets => {
    tweets.forEach(tweet => {
      console.log(`${tweet.author_username}: ${tweet.text}`);
    });
  });
```

## Deployment

### Railway
Add to `railway.json`:
```json
{
  "deploy": {
    "startCommand": "uvicorn api:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Rate Limiting (TODO)
Consider adding rate limiting in production using `slowapi` or similar.

## CORS
CORS is enabled for all origins. Restrict in production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    ...
)
```
