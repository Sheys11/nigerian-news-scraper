import asyncio
from playwright.async_api import async_playwright

async def login_and_save_state():
    """
    Launches a headed Firefox browser for manual login.
    Saves the storage state (cookies, localStorage) to 'twitter_state.json'.
    """
    print("Launching Firefox for manual login...")
    print("Please log in to Twitter/X in the browser window.")
    print("Once logged in, press Enter in this terminal to save the session.")
    
    async with async_playwright() as p:
        # Use Firefox as recommended
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Go to login page
        await page.goto("https://x.com/login")
        
        # Wait for user to log in manually
        input("Press Enter after you have successfully logged in...")
        
        # Save state
        await context.storage_state(path="twitter_state.json")
        print("Session saved to 'twitter_state.json'.")
        print("You can now run the scraper using this session.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_and_save_state())
