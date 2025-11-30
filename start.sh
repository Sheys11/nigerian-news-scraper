#!/bin/bash
# Unified startup script for Railway
# Runs both the API server and the scraper cron job

set -e

echo "Starting Nigerian News Scraper Service..."

# Start the API server in the background
echo "Starting API server..."
uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} &
API_PID=$!

# Wait for API to be ready
sleep 5

# Run the scraper once on startup
echo "Running initial scrape..."
python main.py || echo "Initial scrape failed, will retry on schedule"

# Start the cron-like loop for periodic scraping
echo "Starting scraper cron loop (every 10 minutes)..."
while true; do
    sleep 600  # 10 minutes
    echo "[$(date)] Running scheduled scrape..."
    python main.py || echo "Scrape failed, will retry in 10 minutes"
done &
SCRAPER_PID=$!

# Keep the script running and forward signals
trap "kill $API_PID $SCRAPER_PID; exit" SIGTERM SIGINT

# Wait for API process (main process)
wait $API_PID
