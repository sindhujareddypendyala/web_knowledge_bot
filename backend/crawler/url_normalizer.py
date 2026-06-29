"""
Crawler URL normalization utilities.

Purpose:
    Provides crawler-focused URL normalization, filtering, and same-site checks
    for discovered links before duplicate detection or robots.txt evaluation.

How it connects:
    Crawlers call `URLNormalizer.normalize_discovered_url()` for every href
    found in HTML or sitemap files. The normalizer delegates canonical URL
    cleanup to `utils.validators` and adds crawler policy decisions such as
    same-domain restriction, static asset filtering, and tracking-query removal.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from utils.validators import is_probably_html_url, is_same_domain, normalize_url


@dataclass(frozen=True, slots=True)
class NormalizedURL:
    """Structured result for a discovered URL."""

    original_url: str
    normalized_url: str
    is_internal: bool
    is_html_candidate: bool
    depth: int = 0


class URLNormalizer:
    """Normalize and filter URLs discovered during website crawling."""

    def __init__(
        self,
        base_url: str,
        *,
        include_subdomains: bool = False,
        restrict_to_domain: bool = True,
        strip_tracking: bool = True,
    ) -> None:
        self.base_url = normalize_url(base_url, strip_tracking=strip_tracking)
        self.include_subdomains = include_subdomains
        self.restrict_to_domain = restrict_to_domain
        self.strip_tracking = strip_tracking
        self.base_domain = urlparse(self.base_url).hostname or ""

    def normalize_discovered_url(self, url: str, current_url: str | None = None, depth: int = 0) -> NormalizedURL | None:
        """
        Normalize a discovered URL.

        Returns None when the URL is malformed, outside the configured domain
        policy, or points to a likely static/binary asset.
        """

        try:
            normalized = normalize_url(
                url,
                base_url=current_url or self.base_url,
                strip_tracking=self.strip_tracking,
            )
        except ValueError:
            return None

        internal = is_same_domain(
            normalized,
            self.base_url,
            include_subdomains=self.include_subdomains,
        )
        html_candidate = is_probably_html_url(normalized)

        if self.restrict_to_domain and not internal:
            return None
        if not html_candidate:
            return None

        return NormalizedURL(
            original_url=url,
            normalized_url=normalized,
            is_internal=internal,
            is_html_candidate=html_candidate,
            depth=depth,
        )

    def normalize_many(self, urls: list[str], current_url: str | None = None, depth: int = 0) -> list[NormalizedURL]:
        """Normalize many URLs while preserving first-seen order."""

        seen: set[str] = set()
        normalized_urls: list[NormalizedURL] = []

        for url in urls:
            result = self.normalize_discovered_url(url, current_url=current_url, depth=depth)
            if result is None or result.normalized_url in seen:
                continue
            seen.add(result.normalized_url)
            normalized_urls.append(result)

        return normalized_urls


def normalize_discovered_url(base_url: str, url: str, current_url: str | None = None) -> str | None:
    """Convenience wrapper returning only the normalized URL string."""

    result = URLNormalizer(base_url).normalize_discovered_url(url, current_url=current_url)
    return result.normalized_url if result else None
