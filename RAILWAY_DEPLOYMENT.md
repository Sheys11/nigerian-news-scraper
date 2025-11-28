# Railway Deployment Guide - Nigerian News Scraper

## Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub account (to connect your repository)
- Railway CLI (optional but recommended)

## Option 1: Deploy via Railway Dashboard (Recommended)

### Step 1: Push Code to GitHub
```bash
cd /home/sheys/nigerian-news-scraper

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Nigerian News Scraper"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/nigerian-news-scraper.git
git branch -M main
git push -u origin main
```

### Step 2: Create Railway Project
1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `nigerian-news-scraper` repository

### Step 3: Configure the Project
Railway will auto-detect your project. You need to set up TWO services:

#### Service 1: Scraper (Cron Job)
1. In Railway dashboard, click **"New"** → **"Empty Service"**
2. Name it: `scraper-cron`
3. Go to **Settings** → **Cron Schedule**
4. Set schedule: `*/10 * * * *` (every 10 minutes)
5. Set start command: `python main.py`
6. Click **"Deploy"**

#### Service 2: API Gateway
1. Click **"New"** → **"Empty Service"**
2. Name it: `api-gateway`
3. Go to **Settings**
4. Set start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Under **Networking**, click **"Generate Domain"**
6. Copy the generated URL (e.g., `https://your-app.up.railway.app`)
7. Click **"Deploy"**

### Step 4: Add Database Volume (Optional)
For persistent SQLite storage:
1. In your scraper service, go to **"Volumes"**
2. Click **"New Volume"**
3. Mount path: `/app/data`
4. Update `main.py` to use: `sqlite3.connect("/app/data/nigerian_news.db")`

### Step 5: Monitor Deployment
- Check **"Deployments"** tab for build logs
- Check **"Logs"** tab for runtime logs
- Verify API at: `https://your-app.up.railway.app/health`

## Option 2: Deploy via Railway CLI

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login
```bash
railway login
```

### Step 3: Initialize Project
```bash
cd /home/sheys/nigerian-news-scraper
railway init
```

### Step 4: Deploy
```bash
railway up
```

### Step 5: Set Environment Variables (if needed)
```bash
railway variables set KEY=value
```

### Step 6: Open Dashboard
```bash
railway open
```

## Configuration Files

### Procfile (for Railway)
Create a `Procfile` in your project root:
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
worker: python main.py
```

### railway.toml (Alternative Config)
Create `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn api:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

## Post-Deployment

### Test API Endpoints
```bash
# Replace with your Railway URL
RAILWAY_URL="https://your-app.up.railway.app"

# Health check
curl $RAILWAY_URL/health

# Get stats
curl $RAILWAY_URL/stats

# Get top tweets
curl $RAILWAY_URL/tweets/top?limit=10
```

### Monitor Logs
```bash
railway logs
# Or use the dashboard
```

### Check Database
```bash
railway run sqlite3 nigerian_news.db "SELECT COUNT(*) FROM tweets;"
```

## Troubleshooting

### Build Fails
- Check `railway logs` for errors
- Ensure `requirements.txt` is up to date
- Verify Python version compatibility

### Playwright Issues
Railway may need additional setup for Playwright:
```bash
# Add to railway.toml
[build]
buildCommand = "pip install -r requirements.txt && playwright install-deps && playwright install chromium"
```

### Database Not Persisting
- Add a Railway Volume
- Or use PostgreSQL instead of SQLite:
  ```bash
  railway add postgresql
  ```

### API Not Accessible
- Check if domain is generated under **Networking**
- Verify PORT environment variable is used: `--port $PORT`

## Cost Estimate
- **Hobby Plan**: $5/month (500 hours execution)
- **Pro Plan**: $20/month (unlimited)
- Estimated usage: ~720 hours/month (API) + ~72 hours/month (cron)

## Alternative: Deploy API Only
If you want to run the scraper locally and only deploy the API:

1. Deploy only `api.py` to Railway
2. Run `main.py` locally with cron
3. Use a shared database (PostgreSQL on Railway)

## Next Steps
1. Set up monitoring/alerting
2. Add authentication to API
3. Configure custom domain
4. Set up CI/CD with GitHub Actions
