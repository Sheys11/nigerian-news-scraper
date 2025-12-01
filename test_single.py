import asyncio
import logging
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from main import scrape_account_tweets, init_database, store_tweets

logging.basicConfig(level=logging.INFO)

async def test_run():
    print("Initializing DB...")
    conn = init_database()
    
    async with async_playwright() as p:
        # Use Firefox as per best practices
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        try:
            username = "channelstv"
            print(f"Testing scrape for @{username}...")
            # Pass conn to scrape_account_tweets
            tweets = await scrape_account_tweets(page, username, "news_outlets", conn, max_tweets=10)
            print(f"Collected {len(tweets)} tweets.")
            if tweets:
                store_tweets(conn, tweets)
            for t in tweets:
                print(f"- [{t['created_at']}] {t['text'][:50]}...")
                
        finally:
            await browser.close()
            conn.close()

if __name__ == "__main__":
    asyncio.run(test_run())
