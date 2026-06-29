"""
Search service to discover relevant documentation pages for a technical query.
"""
from __future__ import annotations

import re
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

from services.trusted_sites import get_trusted_prefixes
from utils.logger import get_logger

logger = get_logger(__name__)


async def search_trusted_pages(query: str, domain_key: str, k: int = 5) -> list[str]:
    """
    Search relevant documentation pages for the given domain_key and query.
    Returns the top 3-5 pages. Only returns pages from trusted prefixes.
    """
    prefixes = get_trusted_prefixes(domain_key)
    if not prefixes:
        logger.warning("No trusted site prefixes found for domain: %s", domain_key)
        return []

    # We will search each trusted prefix for the domain
    results: list[str] = []
    for prefix in prefixes:
        # Try DuckDuckGo search first
        urls = await search_duckduckgo(query, prefix, k=k)
        if urls:
            logger.info("DuckDuckGo search returned %d URLs for prefix %s", len(urls), prefix)
            results.extend(urls)
        else:
            # Fallback to local sitemap discovery and keyword filtering
            logger.warning("DuckDuckGo search failed or returned nothing for %s. Using sitemap fallback.", prefix)
            urls = sitemap_fallback_search(query, prefix, k=k)
            logger.info("Sitemap fallback returned %d URLs for prefix %s", len(urls), prefix)
            results.extend(urls)

    # Deduplicate and limit to top k overall
    unique_results: list[str] = []
    for r in results:
        if r not in unique_results:
            unique_results.append(r)

    return unique_results[:k]


async def search_duckduckgo(query: str, site_prefix: str, k: int = 5) -> list[str]:
    """
    Query DuckDuckGo HTML search restricted to site_prefix.
    """
    parsed_prefix = urllib.parse.urlparse(site_prefix)
    domain = parsed_prefix.netloc or site_prefix

    # Clean query and construct search term
    q = f"site:{domain} {query}"
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    params = {"q": q}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logger.warning("DuckDuckGo HTML returned HTTP status %d", response.status)
                    return []
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        links: list[str] = []

        # DuckDuckGo HTML format contains results in links with class 'result__a'
        for a in soup.find_all("a", class_="result__a"):
            href = a.get("href", "")
            if not href:
                continue

            # Handle DuckDuckGo redirect wrapper if present
            # Format: //duckduckgo.com/l/?kh=-1&uddg=https%3A%2F%2Fdocs.python.org%2F3%2F
            if "uddg=" in href:
                parsed_href = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed_href.query)
                if "uddg" in qs:
                    href = qs["uddg"][0]
            elif href.startswith("//"):
                href = "https:" + href

            # Validate that the page belongs to the trusted prefix
            if href.lower().startswith(site_prefix.lower()):
                links.append(href)
                if len(links) >= k:
                    break

        return links
    except Exception as exc:
        logger.warning("DuckDuckGo scraping failed: %s", exc)
        return []


def sitemap_fallback_search(query: str, site_prefix: str, k: int = 5) -> list[str]:
    """
    Fallback method that fetches the sitemap and ranks pages based on token matching
    in the URL path.
    """
    try:
        from crawler.sitemap_loader import SitemapLoader
        loader = SitemapLoader()
        sitemap_res = loader.discover(site_prefix)
        urls = sitemap_res.page_urls

        if not urls:
            return [site_prefix]

        # Process the query into keywords (exclude stop words)
        words = re.findall(r"\w+", query.lower())
        stop_words = {
            "how", "do", "i", "implement", "to", "in", "the", "a", "an", "and", "or",
            "for", "with", "on", "using", "of", "what", "is", "by", "from", "at"
        }
        search_terms = [w for w in words if w not in stop_words and len(w) > 2]
        if not search_terms:
            search_terms = words

        ranked_urls: list[tuple[float, str]] = []
        for url in urls:
            path = urllib.parse.urlparse(url).path.lower()
            # Score url based on keyword occurrences in the URL path
            score = sum(1.0 for term in search_terms if term in path)
            # Add small length penalty to prefer shorter/cleaner URLs
            score -= len(path) * 0.0001
            if score > 0:
                ranked_urls.append((score, url))

        if not ranked_urls:
            # If no matches, return first k URLs in sitemap
            return urls[:k]

        ranked_urls.sort(key=lambda item: item[0], reverse=True)
        return [url for _, url in ranked_urls[:k]]
    except Exception as exc:
        logger.warning("Sitemap fallback search failed: %s", exc)
        return [site_prefix]
