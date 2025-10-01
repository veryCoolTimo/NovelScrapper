"""Browser automation for scraping novel chapters."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NovelScraper:
    """Handles browser automation and page navigation."""

    def __init__(self, headless: bool = config.HEADLESS_MODE, proxy: Optional[str] = None):
        """Initialize the scraper.

        Args:
            headless: Run browser in headless mode
            proxy: Proxy server URL (format: "http://user:pass@host:port")
        """
        self.headless = headless
        self.proxy = proxy or (config.PROXY_SERVER if config.PROXY_ENABLED else None)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser."""
        self.playwright = await async_playwright().start()

        launch_options = {
            "headless": self.headless,
        }

        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}

        self.browser = await self.playwright.chromium.launch(**launch_options)

        context_options = {
            "user_agent": config.USER_AGENT,
            "viewport": config.VIEWPORT,
        }

        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(config.PAGE_LOAD_TIMEOUT)

        logger.info("Browser started successfully")

    async def navigate_to_chapter(self, url: str, retry: int = 0) -> bool:
        """Navigate to a chapter URL.

        Args:
            url: Chapter URL to navigate to
            retry: Current retry attempt number

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            response = await self.page.goto(url, wait_until="networkidle")

            if response.status >= 400:
                logger.error(f"HTTP {response.status} error for {url}")
                if retry < config.MAX_RETRIES:
                    logger.info(f"Retrying... ({retry + 1}/{config.MAX_RETRIES})")
                    await asyncio.sleep(config.RETRY_DELAY)
                    return await self.navigate_to_chapter(url, retry + 1)
                return False

            # Wait for content to load
            await self.wait_for_content_load()
            return True

        except PlaywrightTimeout:
            logger.error(f"Timeout loading {url}")
            if retry < config.MAX_RETRIES:
                logger.info(f"Retrying... ({retry + 1}/{config.MAX_RETRIES})")
                await asyncio.sleep(config.RETRY_DELAY)
                return await self.navigate_to_chapter(url, retry + 1)
            return False

        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            if retry < config.MAX_RETRIES:
                logger.info(f"Retrying... ({retry + 1}/{config.MAX_RETRIES})")
                await asyncio.sleep(config.RETRY_DELAY)
                return await self.navigate_to_chapter(url, retry + 1)
            return False

    async def wait_for_content_load(self, timeout: int = 10000):
        """Wait for chapter content to be loaded.

        Args:
            timeout: Wait timeout in milliseconds
        """
        # Try multiple selectors
        for selector in config.SELECTORS["chapter_content"]:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout, state="visible")
                logger.debug(f"Content loaded with selector: {selector}")
                return
            except PlaywrightTimeout:
                continue

        # If no selector worked, just wait a bit
        logger.warning("No content selector found, waiting 3 seconds...")
        await asyncio.sleep(3)

    async def get_page_html(self) -> str:
        """Get the current page's HTML content.

        Returns:
            HTML content as string
        """
        return await self.page.content()

    async def get_next_chapter_url(self) -> Optional[str]:
        """Try to find the next chapter URL from the page.

        Returns:
            Next chapter URL if found, None otherwise
        """
        for selector in config.SELECTORS["next_chapter"]:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    href = await element.get_attribute("href")
                    if href:
                        # Handle relative URLs
                        if href.startswith("/"):
                            base_url = self.page.url.split("/ru/")[0]
                            href = base_url + href
                        logger.debug(f"Found next chapter URL: {href}")
                        return href
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue

        return None

    async def screenshot(self, path: str = "debug_screenshot.png"):
        """Take a screenshot for debugging.

        Args:
            path: Output path for screenshot
        """
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")

    async def close(self):
        """Close the browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
