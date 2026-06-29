"""
Document domain models for the Website Knowledge Module.

Purpose:
    Defines the canonical in-memory representation for crawled web pages and
    extracted website documents before they are chunked, embedded, stored, or
    exported to another backend module.

How it connects:
    Crawlers return `WebsiteDocument` instances, chunkers convert them into
    LangChain documents, vector stores persist their metadata, and API routes
    serialize them through `to_dict()` without relying on loose dictionaries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ExtractedAsset:
    """Represents a non-text asset extracted from a crawled page."""

    kind: str
    value: str
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "text": self.text,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExtractedAsset":
        return cls(
            kind=str(payload.get("kind", "")),
            value=str(payload.get("value", "")),
            text=str(payload.get("text", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class WebsiteDocument:
    """Cleaned text and metadata for one crawled web page."""

    source_url: str
    title: str
    text: str
    website_id: str | None = None
    canonical_url: str | None = None
    description: str | None = None
    language: str | None = None
    status_code: int | None = None
    content_type: str | None = None
    content_hash: str | None = None
    discovered_from: str | None = None
    depth: int = 0
    crawled_at: str = field(default_factory=utc_now_iso)
    headings: list[str] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    images: list[ExtractedAsset] = field(default_factory=list)
    tables: list[ExtractedAsset] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source_url = self.source_url.strip()
        self.title = self.title.strip() or "Untitled"
        self.text = self.text.strip()

        if self.canonical_url is not None:
            self.canonical_url = self.canonical_url.strip() or None

    @property
    def url(self) -> str:
        """Backward-compatible alias for existing crawler dictionaries."""

        return self.source_url

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def character_count(self) -> int:
        return len(self.text)

    def to_metadata(self) -> dict[str, Any]:
        """Return metadata safe to attach to ChromaDB or LangChain documents."""

        metadata = {
            "source_url": self.source_url,
            "title": self.title,
            "website_id": self.website_id,
            "canonical_url": self.canonical_url,
            "description": self.description,
            "language": self.language,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "discovered_from": self.discovered_from,
            "depth": self.depth,
            "crawled_at": self.crawled_at,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "headings": json.dumps(self.headings, ensure_ascii=False),
            "links": json.dumps(self.links, ensure_ascii=False),
        }
        metadata.update(self.metadata)
        return {key: value for key, value in metadata.items() if value is not None}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "url": self.source_url,
            "title": self.title,
            "text": self.text,
            "website_id": self.website_id,
            "canonical_url": self.canonical_url,
            "description": self.description,
            "language": self.language,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "discovered_from": self.discovered_from,
            "depth": self.depth,
            "crawled_at": self.crawled_at,
            "headings": self.headings,
            "code_blocks": self.code_blocks,
            "images": [image.to_dict() for image in self.images],
            "tables": [table.to_dict() for table in self.tables],
            "links": self.links,
            "metadata": self.metadata,
            "word_count": self.word_count,
            "character_count": self.character_count,
        }

    def to_langchain_document(self):
        """Convert to a LangChain `Document` lazily to keep imports lightweight."""

        try:
            from langchain_core.documents import Document
        except ImportError:
            try:
                from langchain.schema import Document
            except ImportError:
                class Document:
                    def __init__(self, page_content: str, metadata: dict | None = None) -> None:
                        self.page_content = page_content
                        self.metadata = metadata or {}

        return Document(page_content=self.text, metadata=self.to_metadata())

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WebsiteDocument":
        images = [ExtractedAsset.from_dict(item) for item in payload.get("images", [])]
        tables = [ExtractedAsset.from_dict(item) for item in payload.get("tables", [])]

        return cls(
            source_url=str(payload.get("source_url") or payload.get("url") or ""),
            title=str(payload.get("title") or "Untitled"),
            text=str(payload.get("text") or payload.get("page_content") or ""),
            website_id=payload.get("website_id"),
            canonical_url=payload.get("canonical_url"),
            description=payload.get("description"),
            language=payload.get("language"),
            status_code=payload.get("status_code"),
            content_type=payload.get("content_type"),
            content_hash=payload.get("content_hash"),
            discovered_from=payload.get("discovered_from"),
            depth=int(payload.get("depth", 0)),
            crawled_at=str(payload.get("crawled_at") or utc_now_iso()),
            headings=list(payload.get("headings", [])),
            code_blocks=list(payload.get("code_blocks", [])),
            images=images,
            tables=tables,
            links=list(payload.get("links", [])),
            metadata=dict(payload.get("metadata", {})),
        )

    @classmethod
    def from_langchain_document(cls, document: Any) -> "WebsiteDocument":
        metadata = dict(getattr(document, "metadata", {}) or {})
        return cls(
            source_url=str(metadata.get("source_url") or metadata.get("url") or ""),
            title=str(metadata.get("title") or "Untitled"),
            text=str(getattr(document, "page_content", "")),
            website_id=metadata.get("website_id"),
            canonical_url=metadata.get("canonical_url"),
            description=metadata.get("description"),
            language=metadata.get("language"),
            status_code=metadata.get("status_code"),
            content_type=metadata.get("content_type"),
            content_hash=metadata.get("content_hash"),
            discovered_from=metadata.get("discovered_from"),
            depth=int(metadata.get("depth", 0)),
            crawled_at=str(metadata.get("crawled_at") or utc_now_iso()),
            headings=list(metadata.get("headings", [])),
            links=list(metadata.get("links", [])),
            metadata={
                key: value
                for key, value in metadata.items()
                if key
                not in {
                    "source_url",
                    "url",
                    "title",
                    "website_id",
                    "canonical_url",
                    "description",
                    "language",
                    "status_code",
                    "content_type",
                    "content_hash",
                    "discovered_from",
                    "depth",
                    "crawled_at",
                    "headings",
                    "links",
                }
            },
        )
