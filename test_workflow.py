"""Quick test of complete workflow with just 2 accounts"""
import asyncio
from main import main, ACCOUNTS

# Temporarily limit to just 2 accounts for testing
ACCOUNTS_BACKUP = ACCOUNTS.copy()
ACCOUNTS.clear()
ACCOUNTS["news_outlets"] = ["channelstv", "guardian"]

if __name__ == "__main__":
    asyncio.run(main())
