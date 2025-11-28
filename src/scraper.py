import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from .config import HEADLESS, MAX_TWEETS_PER_ACCOUNT
from .analyzer import parse_metric, calculate_relevance_score, filter_tweet
from .database import save_tweet

logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self):
        """Start the browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()

    async def stop(self):
        """Stop the browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_profile(self, username, category):
        """Scrape tweets from a specific profile"""
        url = f"https://x.com/{username}"
        logger.info(f"Scraping {username} ({category})...")
        
        try:
            # Use domcontentloaded to be faster, and add some random delay
            await self.page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Check for potential "Retry" button or "Something went wrong"
            try:
                retry_button = await self.page.query_selector('text="Retry"')
                if retry_button:
                    logger.info("Found Retry button, clicking...")
                    await retry_button.click()
                    await self.page.wait_for_load_state('domcontentloaded')
            except Exception:
                pass

            # Wait for articles or at least the timeline
            try:
                await self.page.wait_for_selector('article', timeout=20000)
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout waiting for articles on {username}")
                # Take screenshot for debug (optional, but good for local)
                # await self.page.screenshot(path=f"debug_{username}.png")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to load profile {username}: {e}")
            return 0

        tweets_collected = 0
        last_height = 0
        consecutive_no_new_tweets = 0
        processed_ids = set()

        while tweets_collected < MAX_TWEETS_PER_ACCOUNT:
            # Get all visible articles
            articles = await self.page.query_selector_all('article')
            
            new_tweets_in_batch = 0
            
            for article in articles:
                try:
                    # Extract Tweet Text
                    text_el = await article.query_selector('[data-testid="tweetText"]')
                    if not text_el:
                        continue
                    text = await text_el.inner_text()
                    
                    # Extract Timestamp/ID/URL
                    time_el = await article.query_selector('time')
                    if not time_el:
                        continue
                    timestamp_str = await time_el.get_attribute('datetime')
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Get Tweet ID and URL from the time element's parent anchor
                    link_el = await article.query_selector('a[href*="/status/"]')
                    if not link_el:
                        continue
                    href = await link_el.get_attribute('href')
                    tweet_id = href.split('/status/')[-1]
                    tweet_url = f"https://x.com{href}"
                    
                    if tweet_id in processed_ids:
                        continue
                    processed_ids.add(tweet_id)

                    # Extract Metrics
                    # Metrics are usually in a group with role="group"
                    # We look for aria-labels or text content
                    metrics_group = await article.query_selector('[role="group"]')
                    likes = 0
                    retweets = 0
                    replies = 0
                    
                    if metrics_group:
                        # This is a heuristic - selectors change often
                        # We look for elements with testids like "reply", "retweet", "like"
                        reply_el = await metrics_group.query_selector('[data-testid="reply"]')
                        retweet_el = await metrics_group.query_selector('[data-testid="retweet"]')
                        like_el = await metrics_group.query_selector('[data-testid="like"]')
                        
                        if reply_el:
                            replies = parse_metric(await reply_el.get_attribute('aria-label') or await reply_el.inner_text())
                        if retweet_el:
                            retweets = parse_metric(await retweet_el.get_attribute('aria-label') or await retweet_el.inner_text())
                        if like_el:
                            likes = parse_metric(await like_el.get_attribute('aria-label') or await like_el.inner_text())

                    total_engagement = likes + retweets + replies
                    relevance_score = calculate_relevance_score(text)

                    tweet_data = {
                        'tweet_id': tweet_id,
                        'author_username': username,
                        'category': category,
                        'text': text,
                        'likes': likes,
                        'retweets': retweets,
                        'replies': replies,
                        'total_engagement': total_engagement,
                        'url': tweet_url,
                        'timestamp': timestamp,
                        'relevance_score': relevance_score
                    }

                    # Filter
                    if filter_tweet(tweet_data):
                        saved = await save_tweet(tweet_data)
                        if saved:
                            tweets_collected += 1
                            new_tweets_in_batch += 1
                            
                    if tweets_collected >= MAX_TWEETS_PER_ACCOUNT:
                        break
                        
                except Exception as e:
                    # logger.warning(f"Error parsing tweet: {e}")
                    continue

            if new_tweets_in_batch == 0:
                consecutive_no_new_tweets += 1
                if consecutive_no_new_tweets > 3:
                    break
            else:
                consecutive_no_new_tweets = 0

            # Scroll down
            await self.page.evaluate('window.scrollBy(0, 2000)')
            await asyncio.sleep(2) # Wait for load
            
            # Check if we reached bottom
            # new_height = await self.page.evaluate('document.body.scrollHeight')
            # if new_height == last_height:
            #     break
            # last_height = new_height

        if tweets_collected == 0:
            logger.warning(f"No tweets collected for {username}. Taking screenshot and dumping HTML...")
            await self.page.screenshot(path=f"debug_{username}.png")
            content = await self.page.content()
            with open(f"debug_{username}.html", "w", encoding="utf-8") as f:
                f.write(content)
            
        logger.info(f"Collected {tweets_collected} tweets from {username}")
        return tweets_collected
