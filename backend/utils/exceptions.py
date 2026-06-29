"""
Custom exception hierarchy for the Website Knowledge Module.

Purpose:
    Converts crawler, parser, embedding, vector-store, retrieval, cache, and
    website-management failures into typed application errors.

How it connects:
    FastAPI routes can catch `WebsiteKnowledgeError` and serialize
    `to_dict()` into consistent API responses. Lower-level modules can raise
    specific subclasses to keep business logic clear without hardcoding HTTP
    response shapes inside crawlers or vector-store classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any


@dataclass(slots=True)
class WebsiteKnowledgeError(Exception):
    """Base exception for all expected module-level failures."""

    message: str
    error_code: str = "WEBSITE_KNOWLEDGE_ERROR"
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(WebsiteKnowledgeError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST,
            details=details or {},
        )


class InvalidURLError(ValidationError):
    def __init__(self, url: str) -> None:
        super().__init__("The provided URL is invalid.", details={"url": url})
        self.error_code = "INVALID_URL"


class RobotsDisallowedError(WebsiteKnowledgeError):
    def __init__(self, url: str) -> None:
        super().__init__(
            message="Crawling this URL is disallowed by robots.txt.",
            error_code="ROBOTS_DISALLOWED",
            status_code=HTTPStatus.FORBIDDEN,
            details={"url": url},
        )


class CrawlError(WebsiteKnowledgeError):
    def __init__(self, message: str, url: str | None = None, details: dict[str, Any] | None = None) -> None:
        payload = details or {}
        if url:
            payload["url"] = url
        super().__init__(
            message=message,
            error_code="CRAWL_ERROR",
            status_code=HTTPStatus.BAD_GATEWAY,
            details=payload,
        )


class FetchError(CrawlError):
    def __init__(self, url: str, reason: str, status_code: int | None = None) -> None:
        details: dict[str, Any] = {"reason": reason}
        if status_code is not None:
            details["upstream_status_code"] = status_code
        super().__init__("Failed to fetch the requested page.", url=url, details=details)
        self.error_code = "FETCH_ERROR"


class SitemapError(CrawlError):
    def __init__(self, url: str, reason: str) -> None:
        super().__init__("Failed to process sitemap.", url=url, details={"reason": reason})
        self.error_code = "SITEMAP_ERROR"


class ParseError(WebsiteKnowledgeError):
    def __init__(self, message: str, url: str | None = None) -> None:
        details = {"url": url} if url else {}
        super().__init__(
            message=message,
            error_code="PARSE_ERROR",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details=details,
        )


class EmptyContentError(ParseError):
    def __init__(self, url: str) -> None:
        super().__init__("No usable page content was found after cleaning.", url=url)
        self.error_code = "EMPTY_CONTENT"


class ChunkingError(WebsiteKnowledgeError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="CHUNKING_ERROR",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details=details or {},
        )


class EmbeddingError(WebsiteKnowledgeError):
    def __init__(self, message: str, provider: str | None = None) -> None:
        details = {"provider": provider} if provider else {}
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details,
        )


class VectorStoreError(WebsiteKnowledgeError):
    def __init__(self, message: str, collection_name: str | None = None) -> None:
        details = {"collection_name": collection_name} if collection_name else {}
        super().__init__(
            message=message,
            error_code="VECTOR_STORE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
        )


class RetrievalError(WebsiteKnowledgeError):
    def __init__(self, message: str, query: str | None = None) -> None:
        details = {"query": query} if query else {}
        super().__init__(
            message=message,
            error_code="RETRIEVAL_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
        )


class WebsiteNotFoundError(WebsiteKnowledgeError):
    def __init__(self, website_id: str) -> None:
        super().__init__(
            message="Indexed website was not found.",
            error_code="WEBSITE_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details={"website_id": website_id},
        )


class WebsiteNotReadyError(WebsiteKnowledgeError):
    def __init__(self, message: str = "No indexed website is ready for retrieval.") -> None:
        super().__init__(
            message=message,
            error_code="WEBSITE_NOT_READY",
            status_code=HTTPStatus.CONFLICT,
            details={},
        )


class DuplicateWebsiteError(WebsiteKnowledgeError):
    def __init__(self, url: str, website_id: str) -> None:
        super().__init__(
            message="This website has already been indexed.",
            error_code="DUPLICATE_WEBSITE",
            status_code=HTTPStatus.CONFLICT,
            details={"url": url, "website_id": website_id},
        )


class CacheError(WebsiteKnowledgeError):
    def __init__(self, message: str, key: str | None = None) -> None:
        details = {"key": key} if key else {}
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
        )


class IntegrationError(WebsiteKnowledgeError):
    def __init__(self, message: str, target: str | None = None) -> None:
        details = {"target": target} if target else {}
        super().__init__(
            message=message,
            error_code="INTEGRATION_ERROR",
            status_code=HTTPStatus.BAD_GATEWAY,
            details=details,
        )
