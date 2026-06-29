"""
Chunk domain models for the Website Knowledge Module.

Purpose:
    Defines the canonical representation of indexed text chunks and retrieved
    context snippets, including source metadata, similarity scores, confidence,
    and export-friendly serialization.

How it connects:
    The website chunker creates `WebsiteChunk` objects, vector-store code stores
    their content and metadata in ChromaDB, retrievers return
    `RetrievedChunk` objects, and backend integrations export those results as
    plain dictionaries.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def build_chunk_id(source_url: str, text: str, chunk_index: int) -> str:
    """Create a deterministic chunk ID from source URL, index, and content."""

    raw = f"{source_url}:{chunk_index}:{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def distance_to_confidence(distance: float | None) -> float:
    """
    Convert a vector distance into a bounded confidence score.

    Chroma returns lower distances for better matches. This simple transform is
    deterministic, monotonic, and API-friendly without pretending to be a model
    probability.
    """

    if distance is None:
        return 0.0
    if distance < 0:
        return 1.0
    return round(1.0 / (1.0 + distance), 4)


@dataclass(slots=True)
class WebsiteChunk:
    """A chunk of cleaned website text ready for embedding and storage."""

    chunk_id: str
    website_id: str
    source_url: str
    title: str
    text: str
    chunk_index: int
    start_char: int | None = None
    end_char: int | None = None
    token_count: int | None = None
    word_count: int | None = None
    content_hash: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source_url = self.source_url.strip()
        self.title = self.title.strip() or "Untitled"
        self.text = self.text.strip()

        if self.word_count is None:
            self.word_count = len(self.text.split())
        if self.content_hash is None:
            self.content_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        website_id: str,
        source_url: str,
        title: str,
        text: str,
        chunk_index: int,
        **kwargs: Any,
    ) -> "WebsiteChunk":
        return cls(
            chunk_id=build_chunk_id(source_url, text, chunk_index),
            website_id=website_id,
            source_url=source_url,
            title=title,
            text=text,
            chunk_index=chunk_index,
            **kwargs,
        )

    def to_metadata(self) -> dict[str, Any]:
        """Return metadata safe for ChromaDB scalar storage."""

        metadata = {
            "chunk_id": self.chunk_id,
            "website_id": self.website_id,
            "source_url": self.source_url,
            "title": self.title,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "token_count": self.token_count,
            "word_count": self.word_count,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
        }

        for key, value in self.metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                metadata[key] = value
            else:
                metadata[key] = json.dumps(value, ensure_ascii=False, default=str)

        return {key: value for key, value in metadata.items() if value is not None}

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "website_id": self.website_id,
            "source_url": self.source_url,
            "title": self.title,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "token_count": self.token_count,
            "word_count": self.word_count,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def to_langchain_document(self):
        """Convert to a LangChain `Document` lazily."""

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
    def from_dict(cls, payload: dict[str, Any]) -> "WebsiteChunk":
        return cls(
            chunk_id=str(payload.get("chunk_id") or ""),
            website_id=str(payload.get("website_id") or ""),
            source_url=str(payload.get("source_url") or payload.get("url") or ""),
            title=str(payload.get("title") or "Untitled"),
            text=str(payload.get("text") or payload.get("page_content") or ""),
            chunk_index=int(payload.get("chunk_index", 0)),
            start_char=payload.get("start_char"),
            end_char=payload.get("end_char"),
            token_count=payload.get("token_count"),
            word_count=payload.get("word_count"),
            content_hash=payload.get("content_hash"),
            created_at=str(payload.get("created_at") or utc_now_iso()),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class RetrievedChunk:
    """A retrieved chunk with ranking data for RAG context export."""

    chunk: WebsiteChunk
    rank: int
    distance: float | None = None
    confidence: float | None = None
    retrieval_method: str = "vector"
    matched_terms: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.confidence is None:
            self.confidence = distance_to_confidence(self.distance)

    @property
    def text(self) -> str:
        return self.chunk.text

    @property
    def source_url(self) -> str:
        return self.chunk.source_url

    @property
    def title(self) -> str:
        return self.chunk.title

    def to_context_dict(self) -> dict[str, Any]:
        """Return the compact shape expected by another backend module."""

        return {
            "text": self.chunk.text,
            "source_url": self.chunk.source_url,
            "title": self.chunk.title,
            "chunk_id": self.chunk.chunk_id,
            "website_id": self.chunk.website_id,
            "rank": self.rank,
            "confidence": self.confidence,
            "retrieval_method": self.retrieval_method,
            "metadata": self.chunk.to_metadata(),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_context_dict()
        payload.update(
            {
                "distance": self.distance,
                "matched_terms": self.matched_terms,
                "chunk": self.chunk.to_dict(),
            }
        )
        return payload

    @classmethod
    def from_langchain_result(
        cls,
        document: Any,
        rank: int,
        distance: float | None = None,
        retrieval_method: str = "vector",
    ) -> "RetrievedChunk":
        metadata = dict(getattr(document, "metadata", {}) or {})
        chunk = WebsiteChunk(
            chunk_id=str(metadata.get("chunk_id") or build_chunk_id(
                str(metadata.get("source_url") or ""),
                str(getattr(document, "page_content", "")),
                int(metadata.get("chunk_index", rank - 1)),
            )),
            website_id=str(metadata.get("website_id") or ""),
            source_url=str(metadata.get("source_url") or ""),
            title=str(metadata.get("title") or "Untitled"),
            text=str(getattr(document, "page_content", "")),
            chunk_index=int(metadata.get("chunk_index", rank - 1)),
            start_char=metadata.get("start_char"),
            end_char=metadata.get("end_char"),
            token_count=metadata.get("token_count"),
            word_count=metadata.get("word_count"),
            content_hash=metadata.get("content_hash"),
            created_at=str(metadata.get("created_at") or utc_now_iso()),
            metadata={
                key: value
                for key, value in metadata.items()
                if key
                not in {
                    "chunk_id",
                    "website_id",
                    "source_url",
                    "title",
                    "chunk_index",
                    "start_char",
                    "end_char",
                    "token_count",
                    "word_count",
                    "content_hash",
                    "created_at",
                }
            },
        )
        return cls(
            chunk=chunk,
            rank=rank,
            distance=distance,
            retrieval_method=retrieval_method,
        )
