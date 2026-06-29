"""
Central configuration for the Website Knowledge Module.

Purpose:
    This file is the single source of truth for environment variables,
    filesystem paths, crawler limits, embedding providers, ChromaDB settings,
    retrieval defaults, and API metadata.

How it connects:
    Crawlers, chunkers, embedding loaders, vector stores, API routes, and
    backend integrations import this module instead of hardcoding operational
    values. Legacy module-level constants are preserved so the existing CLI
    pipeline continues to run while the FastAPI module is added file by file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


EmbeddingProvider = Literal["google", "huggingface", "auto"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _get_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_int(name: str, default: int, minimum: int | None = None) -> int:
    raw_value = _get_str(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from exc

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _get_float(name: str, default: float, minimum: float | None = None) -> float:
    raw_value = _get_str(name, str(default))
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a float, got {raw_value!r}") from exc

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    raw_value = _get_str(name, str(default)).lower()
    if raw_value in {"1", "true", "yes", "y", "on"}:
        return True
    if raw_value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value, got {raw_value!r}")


def _get_literal(name: str, default: str, allowed: set[str]) -> str:
    raw_value = _get_str(name, default)
    allowed_by_lower = {item.lower(): item for item in allowed}
    value_key = raw_value.lower()
    if value_key not in allowed_by_lower:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {allowed_values}")
    return allowed_by_lower[value_key]


@dataclass(frozen=True)
class Settings:
    """Typed application settings loaded from `.env` and process env vars."""

    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)

    app_name: str = field(default_factory=lambda: _get_str("APP_NAME", "Website Knowledge RAG"))
    app_version: str = field(default_factory=lambda: _get_str("APP_VERSION", "1.0.0"))
    environment: str = field(default_factory=lambda: _get_str("ENVIRONMENT", "development"))
    log_level: LogLevel = field(
        default_factory=lambda: _get_literal(
            "LOG_LEVEL",
            "INFO",
            {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
        ).upper()
    )

    google_api_key: str = field(default_factory=lambda: _get_str("GOOGLE_API_KEY"))
    embedding_provider: EmbeddingProvider = field(
        default_factory=lambda: _get_literal(
            "EMBEDDING_PROVIDER",
            "auto",
            {"google", "huggingface", "auto"},
        )
    )
    google_embedding_model: str = field(
        default_factory=lambda: _get_str("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
    )
    google_chat_model: str = field(
        default_factory=lambda: _get_str("GOOGLE_CHAT_MODEL", "gemini-2.0-flash")
    )
    huggingface_embedding_model: str = field(
        default_factory=lambda: _get_str(
            "HUGGINGFACE_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    default_collection_name: str = field(
        default_factory=lambda: _get_str("DEFAULT_COLLECTION_NAME", "website_knowledge")
    )
    retrieval_top_k: int = field(default_factory=lambda: _get_int("RETRIEVAL_TOP_K", 5, minimum=1))
    hybrid_keyword_weight: float = field(
        default_factory=lambda: _get_float("HYBRID_KEYWORD_WEIGHT", 0.35, minimum=0.0)
    )
    hybrid_vector_weight: float = field(
        default_factory=lambda: _get_float("HYBRID_VECTOR_WEIGHT", 0.65, minimum=0.0)
    )

    chunk_size: int = field(default_factory=lambda: _get_int("CHUNK_SIZE", 1000, minimum=100))
    chunk_overlap: int = field(default_factory=lambda: _get_int("CHUNK_OVERLAP", 200, minimum=0))

    max_pages_per_site: int = field(
        default_factory=lambda: _get_int("MAX_PAGES_PER_SITE", 25, minimum=1)
    )
    max_depth: int = field(default_factory=lambda: _get_int("MAX_CRAWL_DEPTH", 3, minimum=0))
    crawl_delay_seconds: float = field(
        default_factory=lambda: _get_float("CRAWL_DELAY_SECONDS", 0.5, minimum=0.0)
    )
    request_timeout_seconds: float = field(
        default_factory=lambda: _get_float("REQUEST_TIMEOUT_SECONDS", 15.0, minimum=1.0)
    )
    retry_attempts: int = field(default_factory=lambda: _get_int("RETRY_ATTEMPTS", 3, minimum=0))
    retry_backoff_seconds: float = field(
        default_factory=lambda: _get_float("RETRY_BACKOFF_SECONDS", 1.5, minimum=0.0)
    )
    async_concurrency: int = field(default_factory=lambda: _get_int("ASYNC_CONCURRENCY", 8, minimum=1))
    respect_robots_txt: bool = field(default_factory=lambda: _get_bool("RESPECT_ROBOTS_TXT", True))
    read_sitemap: bool = field(default_factory=lambda: _get_bool("READ_SITEMAP", True))
    user_agent: str = field(
        default_factory=lambda: _get_str(
            "USER_AGENT",
            "WebsiteKnowledgeRAGBot/1.0 (+https://example.com/bot)",
        )
    )

    cache_enabled: bool = field(default_factory=lambda: _get_bool("CACHE_ENABLED", True))
    cache_ttl_seconds: int = field(default_factory=lambda: _get_int("CACHE_TTL_SECONDS", 86400, minimum=0))

    @property
    def website_docs_path(self) -> Path:
        return self.base_dir / "website_docs"

    @property
    def vector_db_path(self) -> Path:
        return self.base_dir / "vector_db"

    @property
    def temp_path(self) -> Path:
        return self.base_dir / "temp"

    @property
    def uploads_path(self) -> Path:
        return self.base_dir / "uploads"

    @property
    def chat_history_path(self) -> Path:
        return self.base_dir / "chat_history"

    @property
    def logs_path(self) -> Path:
        return self.base_dir / "logs"

    def ensure_runtime_directories(self) -> None:
        for path in (
            self.website_docs_path,
            self.vector_db_path,
            self.temp_path,
            self.uploads_path,
            self.chat_history_path,
            self.logs_path,
        ):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_runtime_directories()

# Backward-compatible constants used by the current modules.
BASE_DIR = str(settings.base_dir)
GOOGLE_API_KEY = settings.google_api_key

WEBSITE_DOCS_PATH = str(settings.website_docs_path)
VECTOR_DB_PATH = str(settings.vector_db_path)
TEMP_PATH = str(settings.temp_path)
UPLOADS_PATH = str(settings.uploads_path)
CHAT_HISTORY_PATH = str(settings.chat_history_path)
LOGS_PATH = str(settings.logs_path)

CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap

MAX_PAGES_PER_SITE = settings.max_pages_per_site
MAX_CRAWL_DEPTH = settings.max_depth
CRAWL_DELAY_SECONDS = settings.crawl_delay_seconds
REQUEST_TIMEOUT_SECONDS = settings.request_timeout_seconds
RETRY_ATTEMPTS = settings.retry_attempts
RETRY_BACKOFF_SECONDS = settings.retry_backoff_seconds
ASYNC_CONCURRENCY = settings.async_concurrency
RESPECT_ROBOTS_TXT = settings.respect_robots_txt
READ_SITEMAP = settings.read_sitemap
USER_AGENT = settings.user_agent

EMBEDDING_PROVIDER = settings.embedding_provider
EMBEDDING_MODEL = settings.google_embedding_model
GOOGLE_EMBEDDING_MODEL = settings.google_embedding_model
GOOGLE_CHAT_MODEL = settings.google_chat_model
HUGGINGFACE_EMBEDDING_MODEL = settings.huggingface_embedding_model

DEFAULT_COLLECTION_NAME = settings.default_collection_name
RETRIEVAL_TOP_K = settings.retrieval_top_k
HYBRID_KEYWORD_WEIGHT = settings.hybrid_keyword_weight
HYBRID_VECTOR_WEIGHT = settings.hybrid_vector_weight

CACHE_ENABLED = settings.cache_enabled
CACHE_TTL_SECONDS = settings.cache_ttl_seconds
