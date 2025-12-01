# Railway Deployment Guide - Nigerian News Scraper (Unified Service)

## Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub account (to connect your repository)

## Deployment Steps

### Step 1: Generate Authentication File (CRITICAL)
Twitter now requires a logged-in session for reliable scraping.
1. Run the auth setup script locally:
   ```bash
   python auth_setup.py
   ```
2. A Firefox window will open. Log in to your Twitter account manually.
3. Press Enter in your terminal.
4. This will create a `twitter_state.json` file.
5. **IMPORTANT**: You must include this file in your deployment.

### Step 2: Push Code to GitHub
```bash
cd /home/sheys/nigerian-news-scraper

# Ensure twitter_state.json is NOT ignored (if you want to commit it)
# WARNING: This file contains your session cookies. For a private repo, this is okay.
# For a public repo, you should use Railway Variables or a private gist instead.
git add .
git add twitter_state.json -f
git commit -m "Ready for Railway with Auth"

# Push to GitHub
git push origin main
```

### Step 3: Create Railway Project
1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `nigerian-news-scraper` repository

### Step 3: Add PostgreSQL Database
1. In Railway dashboard, click **"New"** → **"Database"** → **"PostgreSQL"**
2. This will create a new Postgres service
3. Once deployed, click on the Postgres service → **"Variables"**
4. Copy the `DATABASE_URL`

### Step 4: Configure Your Service
1. Click on your main service (the one running your code)
2. Go to **"Variables"** → **"New Variable"**
   - Key: `DATABASE_URL`
   - Value: Paste the Postgres URL
3. Go to **"Settings"**
4. Under **"Networking"**, click **"Generate Domain"**
5. Copy the generated URL (e.g., `https://your-app.up.railway.app`)

### Step 5: Deploy
Railway will automatically deploy using the `railway.toml` configuration, which:
- Installs dependencies (including Playwright and Chromium)
- Runs `start.sh` which:
  - Starts the API server on port $PORT
  - Runs the scraper immediately
  - Schedules the scraper to run every 10 minutes

### Step 6: Verify Deployment
1. Check **"Deployments"** tab for build logs
2. Check **"Logs"** tab for runtime logs
3. Visit your API at: `https://your-app.up.railway.app/health`
4. Check the Swagger docs: `https://your-app.up.railway.app/docs`

## Testing Your Deployment

### Check API Health
```bash
curl https://your-app.up.railway.app/health
```

### Get Stats
```bash
curl https://your-app.up.railway.app/stats
```

### Get Recent Tweets
```bash
curl https://your-app.up.railway.app/tweets/recent?limit=10
```

## Monitoring

### View Logs
In Railway dashboard → Your Service → **"Logs"**

Look for:
- `Starting API server...` - API is starting
- `Running initial scrape...` - First scrape on startup
- `Running scheduled scrape...` - Periodic scrapes (every 10 min)

### Check Database
In Railway dashboard → PostgreSQL service → **"Data"** tab

You can run SQL queries directly:
```sql
SELECT COUNT(*) FROM tweets;
SELECT * FROM tweets ORDER BY created_at DESC LIMIT 10;
```

## Troubleshooting

### Build Fails
- Check logs for errors
- Ensure `requirements.txt` is correct
- Verify Playwright installation in build command

### Scraper Not Running
- Check logs for Python errors
- Verify `DATABASE_URL` is set correctly
- Check if Chromium installed properly

### API Not Accessible
- Verify domain is generated under **Networking**
- Check if PORT environment variable is used correctly
- Ensure service is running (check logs)

### Database Connection Issues
- Verify `DATABASE_URL` is copied correctly
- Check PostgreSQL service is running
- Ensure both services are in the same Railway project

## Cost Estimate
- **Hobby Plan**: $5/month (500 hours execution)
- **Pro Plan**: $20/month (unlimited)
- Estimated usage: ~720 hours/month (continuous API + periodic scraper)

## Scaling

### Increase Scraper Frequency
Edit `start.sh` and change `sleep 600` to a different value:
- `sleep 300` = 5 minutes
- `sleep 1800` = 30 minutes

### Add More Accounts
Edit `main.py` and add accounts to the `ACCOUNTS` dictionary.

### Optimize Performance
- Reduce `TIME_WINDOW_MINUTES` if you only need very recent tweets
- Adjust `MAX_TWEETS_PER_ACCOUNT` in the scraper logic

## Alternative: Use Railway Cron (Beta)
Railway now supports native cron jobs. If available:
1. Create two services:
   - **API**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Scraper**: `python main.py` (with cron schedule `*/10 * * * *`)
2. Both services share the same `DATABASE_URL`

This approach separates concerns but costs slightly more.
