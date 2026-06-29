"""
Website domain models for the Website Knowledge Module.

Purpose:
    Defines the canonical representation of an indexed website, including
    crawl state, Chroma collection metadata, refresh timestamps, and aggregate
    statistics.

How it connects:
    The website manager persists `WebsiteRecord` objects, crawlers update their
    status and counters, API routes serialize them for `/websites` and
    `/statistics`, and vector-store code uses their `collection_name` to keep
    multiple websites isolated.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


class WebsiteStatus(StrEnum):
    """Lifecycle state for a website inside the indexing pipeline."""

    PENDING = "pending"
    CRAWLING = "crawling"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    REFRESHING = "refreshing"
    DELETED = "deleted"


@dataclass(slots=True)
class WebsiteStatistics:
    """Aggregate counters collected during crawl and indexing."""

    pages_discovered: int = 0
    pages_crawled: int = 0
    pages_failed: int = 0
    pages_skipped: int = 0
    chunks_indexed: int = 0
    images_extracted: int = 0
    tables_extracted: int = 0
    code_blocks_extracted: int = 0
    broken_links: int = 0
    total_words: int = 0
    total_characters: int = 0

    @property
    def success_rate(self) -> float:
        if self.pages_discovered == 0:
            return 0.0
        return round(self.pages_crawled / self.pages_discovered, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pages_discovered": self.pages_discovered,
            "pages_crawled": self.pages_crawled,
            "pages_failed": self.pages_failed,
            "pages_skipped": self.pages_skipped,
            "chunks_indexed": self.chunks_indexed,
            "images_extracted": self.images_extracted,
            "tables_extracted": self.tables_extracted,
            "code_blocks_extracted": self.code_blocks_extracted,
            "broken_links": self.broken_links,
            "total_words": self.total_words,
            "total_characters": self.total_characters,
            "success_rate": self.success_rate,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "WebsiteStatistics":
        payload = payload or {}
        return cls(
            pages_discovered=int(payload.get("pages_discovered", 0)),
            pages_crawled=int(payload.get("pages_crawled", 0)),
            pages_failed=int(payload.get("pages_failed", 0)),
            pages_skipped=int(payload.get("pages_skipped", 0)),
            chunks_indexed=int(payload.get("chunks_indexed", 0)),
            images_extracted=int(payload.get("images_extracted", 0)),
            tables_extracted=int(payload.get("tables_extracted", 0)),
            code_blocks_extracted=int(payload.get("code_blocks_extracted", 0)),
            broken_links=int(payload.get("broken_links", 0)),
            total_words=int(payload.get("total_words", 0)),
            total_characters=int(payload.get("total_characters", 0)),
        )


@dataclass(slots=True)
class WebsiteRecord:
    """Persistent metadata for one website indexed by the module."""

    website_id: str
    base_url: str
    normalized_url: str
    domain: str
    collection_name: str
    status: WebsiteStatus = WebsiteStatus.PENDING
    title: str | None = None
    description: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    last_crawled_at: str | None = None
    last_indexed_at: str | None = None
    last_refreshed_at: str | None = None
    last_error: str | None = None
    robots_txt_url: str | None = None
    sitemap_url: str | None = None
    statistics: WebsiteStatistics = field(default_factory=WebsiteStatistics)
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_status(self, status: WebsiteStatus, error: str | None = None) -> None:
        self.status = status
        self.updated_at = utc_now_iso()
        self.last_error = error

        if status == WebsiteStatus.CRAWLING:
            self.last_crawled_at = self.updated_at
        elif status == WebsiteStatus.READY:
            self.last_indexed_at = self.updated_at
        elif status == WebsiteStatus.REFRESHING:
            self.last_refreshed_at = self.updated_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "website_id": self.website_id,
            "base_url": self.base_url,
            "normalized_url": self.normalized_url,
            "domain": self.domain,
            "collection_name": self.collection_name,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_crawled_at": self.last_crawled_at,
            "last_indexed_at": self.last_indexed_at,
            "last_refreshed_at": self.last_refreshed_at,
            "last_error": self.last_error,
            "robots_txt_url": self.robots_txt_url,
            "sitemap_url": self.sitemap_url,
            "statistics": self.statistics.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WebsiteRecord":
        return cls(
            website_id=str(payload["website_id"]),
            base_url=str(payload["base_url"]),
            normalized_url=str(payload["normalized_url"]),
            domain=str(payload["domain"]),
            collection_name=str(payload["collection_name"]),
            status=WebsiteStatus(str(payload.get("status", WebsiteStatus.PENDING))),
            title=payload.get("title"),
            description=payload.get("description"),
            created_at=str(payload.get("created_at") or utc_now_iso()),
            updated_at=str(payload.get("updated_at") or utc_now_iso()),
            last_crawled_at=payload.get("last_crawled_at"),
            last_indexed_at=payload.get("last_indexed_at"),
            last_refreshed_at=payload.get("last_refreshed_at"),
            last_error=payload.get("last_error"),
            robots_txt_url=payload.get("robots_txt_url"),
            sitemap_url=payload.get("sitemap_url"),
            statistics=WebsiteStatistics.from_dict(payload.get("statistics")),
            metadata=dict(payload.get("metadata", {})),
        )


def build_website_id(normalized_url: str) -> str:
    """Create a stable ID for a website from its normalized base URL."""

    digest = hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:12]
    parsed = urlparse(normalized_url)
    domain_slug = slugify(parsed.netloc or "website")
    return f"{domain_slug}-{digest}"


def build_collection_name(website_id: str) -> str:
    """Create a Chroma-safe collection name for one website."""

    collection = f"website_{slugify(website_id)}"
    return collection[:63].strip("_-") or "website_knowledge"


def slugify(value: str) -> str:
    """Convert a string into a lowercase identifier safe for filenames/Chroma."""

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_-")
    return slug or "item"


def create_website_record(base_url: str, normalized_url: str) -> WebsiteRecord:
    """Factory for a new website record with stable ID and collection name."""

    parsed = urlparse(normalized_url)
    domain = parsed.netloc.lower()
    website_id = build_website_id(normalized_url)
    return WebsiteRecord(
        website_id=website_id,
        base_url=base_url,
        normalized_url=normalized_url,
        domain=domain,
        collection_name=build_collection_name(website_id),
        robots_txt_url=f"{parsed.scheme}://{domain}/robots.txt" if parsed.scheme and domain else None,
        sitemap_url=f"{parsed.scheme}://{domain}/sitemap.xml" if parsed.scheme and domain else None,
    )
