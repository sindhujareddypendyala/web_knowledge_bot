"""
Sitemap discovery and parsing for documentation websites.

Reads sitemap hints from robots.txt, common sitemap locations, sitemap indexes,
and regular urlsets. Output is normalized, deduplicated, and ready for robots
filtering / crawler scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

import requests

from config import REQUEST_TIMEOUT_SECONDS, USER_AGENT
from crawler.retry_handler import RetryConfig, RetryHandler
from crawler.robots_handler import RobotsHandler
from utils.logger import get_logger, log_event
from utils.validators import dedupe_urls, normalize_url

logger = get_logger(__name__)

SITEMAP_PATHS = ("/sitemap.xml", "/sitemap_index.xml", "/sitemap/sitemap.xml")
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass(slots=True)
class SitemapResult:
    sitemap_urls: list[str] = field(default_factory=list)
    page_urls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "sitemap_urls": self.sitemap_urls,
            "page_urls": self.page_urls,
            "errors": self.errors,
            "page_count": len(self.page_urls),
        }


class SitemapLoader:
    def __init__(
        self,
        session: requests.Session | None = None,
        robots_handler: RobotsHandler | None = None,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.session = session or requests.Session()
        self.robots_handler = robots_handler or RobotsHandler(session=self.session)
        self.timeout_seconds = timeout_seconds
        self.retry_handler = RetryHandler(RetryConfig(max_attempts=1, base_delay_seconds=0.5))

    def discover(self, base_url: str, max_urls: int | None = None) -> SitemapResult:
        normalized_base = normalize_url(base_url)
        candidates = self._candidate_sitemaps(normalized_base)
        result = SitemapResult(sitemap_urls=candidates)
        pages: list[str] = []

        for sitemap_url in candidates:
            try:
                xml = self.fetch_sitemap(sitemap_url)
                pages.extend(self.extract_urls(xml, max_urls=max_urls))
            except Exception as exc:
                result.errors.append(f"{sitemap_url}: {exc}")
                log_event(logger, "WARNING", "Failed to process sitemap", sitemap_url=sitemap_url, error=str(exc))

            if max_urls and len(pages) >= max_urls:
                break

        result.page_urls = dedupe_urls(pages)[:max_urls]
        return result

    def fetch_sitemap(self, sitemap_url: str) -> str:
        normalized = normalize_url(sitemap_url)

        def _fetch() -> requests.Response:
            return self.session.get(
                normalized,
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout_seconds,
            )

        response = self.retry_handler.run(_fetch, url=normalized, operation_name="fetch sitemap")
        response.raise_for_status()
        text = response.text
        if "<urlset" not in text.lower() and "<sitemapindex" not in text.lower():
            raise ValueError("Response does not look like sitemap XML.")
        return text

    def extract_urls(self, xml: str, max_urls: int | None = None) -> list[str]:
        urls = extract_urls(xml)
        return urls[:max_urls] if max_urls else urls

    def _candidate_sitemaps(self, base_url: str) -> list[str]:
        parsed_base = normalize_url(base_url).rstrip("/")
        root = parsed_base.split("/", 3)
        origin = "/".join(root[:3]) if len(root) >= 3 else parsed_base

        candidates = list(self.robots_handler.get_sitemaps(origin))
        candidates.extend(origin + path for path in SITEMAP_PATHS)
        return dedupe_urls(candidates)


def load_sitemap(url: str) -> str | None:
    """Legacy helper returning the first available sitemap XML."""

    loader = SitemapLoader()
    for sitemap_url in loader._candidate_sitemaps(url):
        try:
            return loader.fetch_sitemap(sitemap_url)
        except Exception:
            continue
    logger.warning("No sitemap found for %s", url)
    return None


def extract_urls(xml: str) -> list[str]:
    """Parse sitemap XML into page URLs, including nested sitemap indexes."""

    if not xml:
        return []

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        logger.warning("Failed to parse sitemap XML: %s", exc)
        return []

    urls: list[str] = []
    for loc in root.findall(".//sm:url/sm:loc", SITEMAP_NS):
        if loc.text:
            urls.append(loc.text.strip())

    for loc in root.findall(".//sm:sitemap/sm:loc", SITEMAP_NS):
        if not loc.text:
            continue
        try:
            nested = requests.get(loc.text.strip(), headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
            nested.raise_for_status()
            urls.extend(extract_urls(nested.text))
        except requests.RequestException as exc:
            logger.warning("Could not fetch nested sitemap %s: %s", loc.text, exc)

    return dedupe_urls(urls)
