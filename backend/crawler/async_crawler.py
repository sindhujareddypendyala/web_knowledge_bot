"""
Async crawler facade.

Uses `asyncio.to_thread` around the production sync crawler so FastAPI can run
crawl jobs without blocking the event loop. This keeps behavior identical while
remaining easy to replace with native aiohttp fetching later.
"""

from __future__ import annotations

import asyncio

from config import CRAWL_DELAY_SECONDS, MAX_CRAWL_DEPTH, MAX_PAGES_PER_SITE
from crawler.crawler import CrawlResult, WebsiteCrawler


class AsyncWebsiteCrawler:
    def __init__(
        self,
        max_pages: int = MAX_PAGES_PER_SITE,
        max_depth: int = MAX_CRAWL_DEPTH,
        delay_seconds: float = CRAWL_DELAY_SECONDS,
    ) -> None:
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds

    async def crawl(self, url: str, website_id: str | None = None) -> CrawlResult:
        crawler = WebsiteCrawler(
            max_pages=self.max_pages,
            max_depth=self.max_depth,
            delay_seconds=self.delay_seconds,
        )
        return await asyncio.to_thread(crawler.crawl, url, website_id)
