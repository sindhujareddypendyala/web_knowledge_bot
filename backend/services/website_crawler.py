"""
Asynchronous website crawler for high-performance parallel page downloads.
"""
from __future__ import annotations

import asyncio
import aiohttp

from services.trusted_sites import is_trusted_url
from services.html_parser import DocumentationHTMLParser
from models.document import WebsiteDocument
from utils.logger import get_logger

logger = get_logger(__name__)


class AsyncWebsiteCrawler:
    """
    Crawls and parses multiple web pages concurrently.
    Enforces trusted URL validation to prevent malicious injection.
    """

    def __init__(self, concurrency: int = 5, timeout_seconds: float = 15.0) -> None:
        self.concurrency = concurrency
        self.timeout_seconds = timeout_seconds
        self.parser = DocumentationHTMLParser()

    async def crawl_pages(
        self,
        urls: list[str],
        website_id: str | None = None,
    ) -> list[WebsiteDocument]:
        """
        Crawls the list of target URLs in parallel.
        Filters out untrusted URLs.
        """
        trusted_urls = [url for url in urls if is_trusted_url(url)]
        untrusted_count = len(urls) - len(trusted_urls)
        if untrusted_count > 0:
            logger.warning(
                "Skipping %d untrusted URLs to prevent security policy violations.",
                untrusted_count,
            )

        if not trusted_urls:
            return []

        semaphore = asyncio.Semaphore(self.concurrency)
        headers = {
            "User-Agent": "WebsiteKnowledgeRAGBot/1.0 (+https://example.com/bot)"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [
                self._crawl_single_page(session, url, semaphore, website_id)
                for url in trusted_urls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        documents: list[WebsiteDocument] = []
        for r in results:
            if isinstance(r, WebsiteDocument):
                documents.append(r)
            elif isinstance(r, Exception):
                logger.error("A page download task encountered an error: %s", r)

        return documents

    async def _crawl_single_page(
        self,
        session: aiohttp.ClientSession,
        url: str,
        semaphore: asyncio.Semaphore,
        website_id: str | None = None,
    ) -> WebsiteDocument | None:
        """
        Crawls and parses a single page under semaphore concurrency control.
        """
        async with semaphore:
            try:
                async with session.get(url, timeout=self.timeout_seconds) as response:
                    if response.status != 200:
                        logger.warning(
                            "Failed to fetch %s (HTTP %d)",
                            url,
                            response.status,
                        )
                        return None

                    content_type = response.headers.get("content-type", "")
                    if "html" not in content_type.lower():
                        logger.warning(
                            "Skipping non-HTML page: %s (content-type: %s)",
                            url,
                            content_type,
                        )
                        return None

                    html = await response.text()
                    doc = self.parser.parse(
                        html=html,
                        url=url,
                        status_code=response.status,
                        content_type=content_type,
                        website_id=website_id,
                    )
                    return doc
            except Exception as exc:
                logger.error("Exception occurred while crawling %s: %s", url, exc)
                raise exc
