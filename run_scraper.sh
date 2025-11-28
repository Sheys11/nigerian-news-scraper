#!/bin/bash
# Nigerian News Scraper - Cron Wrapper Script
# Usage: ./run_scraper.sh

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"
LOG_DIR="$SCRIPT_DIR/logs"
LOCK_FILE="$SCRIPT_DIR/.scraper.lock"
FAILURE_LOG="$LOG_DIR/failures.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check for lock file (prevent concurrent runs)
if [ -f "$LOCK_FILE" ]; then
    echo "$(date): Scraper is already running (lock file exists)" >> "$FAILURE_LOG"
    exit 1
fi

# Create lock file
touch "$LOCK_FILE"

# Cleanup function
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Run the scraper
echo "$(date): Starting scraper..." >> "$LOG_DIR/cron.log"

if python "$PYTHON_SCRIPT"; then
    echo "$(date): Scraper completed successfully" >> "$LOG_DIR/cron.log"
    # Reset failure counter
    echo "0" > "$LOG_DIR/failure_count.txt"
else
    EXIT_CODE=$?
    echo "$(date): Scraper failed with exit code $EXIT_CODE" >> "$FAILURE_LOG"
    
    # Track consecutive failures
    FAILURE_COUNT=$(cat "$LOG_DIR/failure_count.txt" 2>/dev/null || echo "0")
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "$FAILURE_COUNT" > "$LOG_DIR/failure_count.txt"
    
    # Alert if consecutive failures > 3
    if [ "$FAILURE_COUNT" -gt 3 ]; then
        echo "$(date): ALERT - $FAILURE_COUNT consecutive failures!" >> "$FAILURE_LOG"
        # You can add email/Slack notification here
    fi
    
    exit $EXIT_CODE
fi
