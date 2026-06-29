"""
Duplicate detection for website crawling and indexing.

Purpose:
    Tracks already-seen URLs and page content so the crawler avoids fetching,
    processing, chunking, and embedding duplicate material.

How it connects:
    Sitemap loaders and crawlers call `DuplicateDetector.should_visit_url()`
    before scheduling fetches, then call `is_duplicate_content()` after parsing
    and cleaning page text. Website managers can also inspect detector counters
    for crawl statistics.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from utils.validators import normalize_url


def hash_content(text: str) -> str:
    """Return a stable SHA-256 hash for normalized text content."""

    normalized_text = " ".join((text or "").split()).lower()
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class DuplicateStats:
    """Counters describing duplicate filtering decisions."""

    urls_seen: int = 0
    duplicate_urls: int = 0
    content_seen: int = 0
    duplicate_content: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "urls_seen": self.urls_seen,
            "duplicate_urls": self.duplicate_urls,
            "content_seen": self.content_seen,
            "duplicate_content": self.duplicate_content,
        }


@dataclass(slots=True)
class DuplicateDetector:
    """In-memory duplicate detector for one crawl job."""

    seen_urls: set[str] = field(default_factory=set)
    seen_content_hashes: set[str] = field(default_factory=set)
    stats: DuplicateStats = field(default_factory=DuplicateStats)

    def should_visit_url(self, url: str) -> bool:
        """
        Return True if `url` has not been seen in this crawl.

        Invalid URLs are treated as not visitable.
        """

        try:
            normalized = normalize_url(url)
        except ValueError:
            return False

        if normalized in self.seen_urls:
            self.stats.duplicate_urls += 1
            return False

        self.seen_urls.add(normalized)
        self.stats.urls_seen += 1
        return True

    def mark_url_seen(self, url: str) -> str | None:
        """Normalize and mark a URL as seen, returning the normalized value."""

        try:
            normalized = normalize_url(url)
        except ValueError:
            return None

        if normalized not in self.seen_urls:
            self.seen_urls.add(normalized)
            self.stats.urls_seen += 1
        return normalized

    def is_duplicate_url(self, url: str) -> bool:
        """Return True when a normalized URL has already been seen."""

        try:
            normalized = normalize_url(url)
        except ValueError:
            return True
        return normalized in self.seen_urls

    def is_duplicate_content(self, text: str, mark_seen: bool = True) -> bool:
        """
        Return True when cleaned page text duplicates previous page content.

        When `mark_seen` is True, new content hashes are stored immediately.
        """

        digest = hash_content(text)
        if digest in self.seen_content_hashes:
            self.stats.duplicate_content += 1
            return True

        if mark_seen:
            self.seen_content_hashes.add(digest)
            self.stats.content_seen += 1
        return False

    def mark_content_seen(self, text: str) -> str:
        """Hash and mark content as seen, returning the hash."""

        digest = hash_content(text)
        if digest not in self.seen_content_hashes:
            self.seen_content_hashes.add(digest)
            self.stats.content_seen += 1
        return digest

    def reset(self) -> None:
        """Clear detector state and counters."""

        self.seen_urls.clear()
        self.seen_content_hashes.clear()
        self.stats = DuplicateStats()
