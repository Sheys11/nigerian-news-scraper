# Railway Deployment - Quick Fix

## Issue
Playwright browsers weren't installed in production, causing:
```
Executable doesn't exist at /root/.cache/ms-playwright/firefox-1495/firefox/firefox
```

## Solution
Updated `railway.toml` to install Firefox during build:

```toml
[build]
buildCommand = "pip install -r requirements.txt && playwright install-deps && playwright install firefox"
```

## Deploy Steps
1. **Commit changes**:
   ```bash
   git add railway.toml
   git commit -m "Fix: Install Firefox in Railway build"
   git push origin main
   ```

2. **Railway will auto-redeploy** with the new build command

3. **Monitor logs** in Railway dashboard for:
   - `playwright install firefox` success
   - `Starting Nigerian News Scraper Service...`
   - `✓ Scraped X tweets from @channelstv`

## Expected Build Time
- First build: ~3-5 minutes (installing browsers)
- Subsequent builds: ~1-2 minutes (cached)

## Verification
Once deployed, check:
- `/health` endpoint returns 200
- `/stats` shows tweet counts
- Logs show successful scrapes
