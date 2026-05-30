from __future__ import annotations
import structlog
from playwright.async_api import Browser, BrowserContext, async_playwright

logger = structlog.get_logger(__name__)


class BrowserPool:
    """Manages the shared Playwright browser instance and creates isolated contexts."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None

    async def initialize(self) -> None:
        if not self._browser:
            logger.info("initializing_playwright_browser_instance")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

    async def create_context(self) -> BrowserContext:
        await self.initialize()
        logger.info("creating_isolated_browser_context")
        return await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

    async def close(self) -> None:
        if self._browser:
            logger.info("closing_playwright_browser_instance")
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
