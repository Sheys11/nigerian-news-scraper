# Deployment Guide - Nigerian News Scraper

## Local Cron Setup

### 1. Make the wrapper script executable
```bash
chmod +x run_scraper.sh
```

### 2. Test the script manually
```bash
./run_scraper.sh
```

### 3. Install crontab entry
```bash
crontab -e
```

Add this line to run every 10 minutes:
```
*/10 * * * * /home/sheys/nigerian-news-scraper/run_scraper.sh >> /home/sheys/nigerian-news-scraper/logs/cron.log 2>&1
```

### 4. Monitor logs
```bash
tail -f logs/cron.log
tail -f logs/scraper_*.log
tail -f logs/failures.log
```

## Systemd Setup (Alternative to Cron)

### 1. Copy service files
```bash
sudo cp scraper.service /etc/systemd/system/
sudo cp scraper.timer /etc/systemd/system/
```

### 2. Enable and start the timer
```bash
sudo systemctl daemon-reload
sudo systemctl enable scraper.timer
sudo systemctl start scraper.timer
```

### 3. Check status
```bash
sudo systemctl status scraper.timer
sudo systemctl list-timers
```

## Railway Deployment

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login to Railway
```bash
railway login
```

### 3. Initialize project
```bash
railway init
```

### 4. Deploy
```bash
railway up
```

### 5. Set up cron job (Railway Cron)
In Railway dashboard:
- Go to your project
- Add a new service
- Select "Cron Job"
- Set schedule: `*/10 * * * *` (every 10 minutes)
- Set command: `python main.py`

## Monitoring

### Check database
```bash
sqlite3 nigerian_news.db "SELECT COUNT(*) FROM tweets;"
sqlite3 nigerian_news.db "SELECT COUNT(*) FROM tweets WHERE ingested_at > datetime('now', '-1 hour');"
```

### View recent tweets
```bash
sqlite3 nigerian_news.db "SELECT author_username, text, created_at FROM tweets ORDER BY ingested_at DESC LIMIT 10;"
```

### Check for failures
```bash
cat logs/failures.log
cat logs/failure_count.txt
```

## Troubleshooting

### Scraper not running
- Check lock file: `rm .scraper.lock`
- Check cron logs: `grep CRON /var/log/syslog`
- Verify virtual environment: `source .venv/bin/activate && python --version`

### No tweets collected
- Check time window (60 minutes)
- Verify accounts are active
- Check for rate limiting in logs

### High failure rate
- Increase retry delays
- Reduce number of accounts
- Check network connectivity
