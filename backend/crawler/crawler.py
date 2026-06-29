"""
Synchronous website crawler orchestration.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import CRAWL_DELAY_SECONDS, MAX_CRAWL_DEPTH, MAX_PAGES_PER_SITE, REQUEST_TIMEOUT_SECONDS, USER_AGENT
from crawler.duplicate_detector import DuplicateDetector
from crawler.image_extractor import extract_images
from crawler.parser import parse_page
from crawler.robots_handler import RobotsHandler
from crawler.sitemap_loader import SitemapLoader
from crawler.table_extractor import extract_tables
from crawler.url_normalizer import URLNormalizer
from crawler.website_processor import WebsiteProcessor
from models.document import WebsiteDocument
from utils.logger import get_logger, log_event
from utils.validators import ensure_url, is_probably_html_url

logger = get_logger(__name__)


@dataclass(slots=True)
class CrawlResult:
    base_url: str
    documents: list[WebsiteDocument] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)
    broken_links: list[str] = field(default_factory=list)
    discovered_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "base_url": self.base_url,
            "documents": [document.to_dict() for document in self.documents],
            "failed_urls": self.failed_urls,
            "broken_links": self.broken_links,
            "discovered_urls": self.discovered_urls,
            "document_count": len(self.documents),
        }


class WebsiteCrawler:
    def __init__(
        self,
        max_pages: int = MAX_PAGES_PER_SITE,
        max_depth: int = MAX_CRAWL_DEPTH,
        delay_seconds: float = CRAWL_DELAY_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.session = session or requests.Session()
        self.robots = RobotsHandler(session=self.session)
        self.processor = WebsiteProcessor()
        self.detector = DuplicateDetector()

    def crawl(self, url: str, website_id: str | None = None) -> CrawlResult:
        base_url = ensure_url(url)
        normalizer = URLNormalizer(base_url)
        result = CrawlResult(base_url=base_url)
        queue: deque[tuple[str, int]] = deque()

        sitemap_urls = SitemapLoader(session=self.session, robots_handler=self.robots).discover(base_url, max_urls=self.max_pages).page_urls
        sitemap_fallbacks = [url for url in sitemap_urls if url != base_url]
        if self.detector.should_visit_url(base_url):
            queue.append((base_url, 0))

        while queue and len(result.documents) < self.max_pages:
            page_url, depth = queue.popleft()
            if not self.robots.can_fetch(page_url):
                continue

            try:
                document, links = self.crawl_page(page_url, website_id=website_id, depth=depth)
                if self.detector.is_duplicate_content(document.text):
                    continue
                result.documents.append(document)
                result.discovered_urls.append(page_url)

                if depth < self.max_depth:
                    normalized_links = normalizer.normalize_many(links, current_url=page_url, depth=depth + 1)
                    normalized_links.sort(
                        key=lambda item: _link_priority(item.normalized_url, base_url)
                    )
                    for normalized in normalized_links:
                        if len(result.documents) + len(queue) >= self.max_pages:
                            break
                        if self.detector.should_visit_url(normalized.normalized_url):
                            queue.append((normalized.normalized_url, depth + 1))
            except Exception as exc:
                result.failed_urls.append(page_url)
                log_event(logger, "WARNING", "Failed to crawl page", url=page_url, error=str(exc))

            delay = self.robots.get_crawl_delay(page_url, default=self.delay_seconds) or self.delay_seconds
            if delay:
                time.sleep(delay)

            if not queue and sitemap_fallbacks and len(result.documents) < self.max_pages:
                for fallback_url in sitemap_fallbacks:
                    if self.detector.should_visit_url(fallback_url):
                        queue.append((fallback_url, 0))
                    if len(queue) + len(result.documents) >= self.max_pages:
                        break

        return result

    def crawl_page(self, url: str, website_id: str | None = None, depth: int = 0) -> tuple[WebsiteDocument, list[str]]:
        response = self.session.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if content_type and "html" not in content_type.lower():
            raise ValueError(f"Unsupported content type: {content_type}")
        if not is_probably_html_url(url):
            raise ValueError("URL does not look like an HTML page.")

        soup = BeautifulSoup(response.text, "html.parser")
        images = extract_images(soup, url)
        tables = extract_tables(soup)
        final_url = response.url or url
        parsed = parse_page(response.text, final_url)
        processed = self.processor.process_text(
            parsed.text,
            code_blocks=parsed.code_blocks,
            table_texts=[table.text for table in tables],
        )

        document = WebsiteDocument(
            website_id=website_id,
            source_url=final_url,
            title=parsed.metadata.title,
            text=processed.text,
            canonical_url=parsed.metadata.canonical_url,
            description=parsed.metadata.description,
            language=parsed.metadata.language,
            status_code=response.status_code,
            content_type=content_type,
            depth=depth,
            headings=parsed.metadata.headings,
            code_blocks=parsed.code_blocks,
            images=images,
            tables=tables,
            links=parsed.links,
            metadata=parsed.metadata.to_document_metadata() | {"processing": processed.to_dict()},
        )
        return document, parsed.links


def crawl_website(url: str, max_pages: int = MAX_PAGES_PER_SITE, delay: float = CRAWL_DELAY_SECONDS) -> list[dict]:
    """Legacy helper returning dictionaries for the original CLI pipeline."""

    result = WebsiteCrawler(max_pages=max_pages, delay_seconds=delay).crawl(url)
    return [document.to_dict() for document in result.documents]


def fetch_page(url: str) -> str | None:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.error("Failed to fetch %s: %s", url, exc)
        return None


def discover_urls(base_url: str, max_pages: int = MAX_PAGES_PER_SITE) -> list[str]:
    return SitemapLoader().discover(base_url, max_urls=max_pages).page_urls or [ensure_url(base_url)]


def crawl_page(url: str) -> dict | None:
    try:
        document, _ = WebsiteCrawler(max_pages=1).crawl_page(ensure_url(url))
        return document.to_dict()
    except Exception as exc:
        logger.warning("Failed to crawl page %s: %s", url, exc)
        return None


def _link_priority(url: str, base_url: str) -> tuple[int, str]:
    """Prefer links that stay inside the requested documentation subsection."""

    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    base_path = parsed_base.path
    if not base_path.endswith("/"):
        base_path = base_path.rsplit("/", 1)[0] + "/"

    if parsed_url.netloc != parsed_base.netloc:
        return (3, url)
    if parsed_url.path.startswith(base_path):
        return (0, url)
    if parsed_url.path.startswith(parsed_base.path.split("/", 2)[0]):
        return (1, url)
    return (2, url)
