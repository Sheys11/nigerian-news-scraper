import asyncio
import logging
from playwright.async_api import async_playwright
from main import scrape_account_tweets, init_database

logging.basicConfig(level=logging.INFO)

async def test_run_multiple():
    print("Initializing DB...")
    init_database()
    
    # Select one account from each category for testing
    test_accounts = {
        "news_outlets": ["channelstv"],
        "journalists": ["DavidHundeyin"],
        "activists": ["AishaYesufu"],
        "grassroots": ["DrJoeAbah"],
        "commentary": ["Mr_Macaroni"]
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        total_collected = 0
        
        try:
            for category, usernames in test_accounts.items():
                for username in usernames:
                    print(f"\nTesting scrape for @{username} [{category}]...")
                    tweets = await scrape_account_tweets(page, username, category, max_tweets=10)
                    print(f"Collected {len(tweets)} tweets.")
                    total_collected += len(tweets)
                    
                    # Wait between accounts
                    await asyncio.sleep(3)
                    
            print(f"\nTotal collected: {total_collected}")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_run_multiple())
