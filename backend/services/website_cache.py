"""
Website caching service to check indexing status and prevent duplicate page crawls.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from config import WEBSITE_DOCS_PATH, CACHE_TTL_SECONDS


class WebsiteCache:
    """
    File-backed cache mapping URL to crawl timestamp, content hash, and Chroma collection name.
    Supports a configurable TTL to refresh expired entries.
    """

    def __init__(self, cache_file_path: str | Path | None = None) -> None:
        self.cache_file_path = Path(
            cache_file_path or Path(WEBSITE_DOCS_PATH) / "cache.json"
        )
        self.cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load()

    def _load(self) -> dict[str, dict]:
        if not self.cache_file_path.exists():
            return {}
        try:
            with self.cache_file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}

    def _save(self) -> None:
        try:
            with self.cache_file_path.open("w", encoding="utf-8") as file:
                json.dump(self.cache, file, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def is_cached_and_valid(self, url: str, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
        """
        Check if a URL is cached and still fresh.
        """
        record = self.cache.get(url)
        if not record:
            return False

        last_indexed_at = record.get("last_indexed_at", 0.0)
        return (time.time() - last_indexed_at) < ttl_seconds

    def get_collection(self, url: str) -> str | None:
        """
        Get the collection name in which a URL is indexed.
        """
        record = self.cache.get(url)
        return record.get("collection_name") if record else None

    def update(self, url: str, content_hash: str, collection_name: str) -> None:
        """
        Add or update a cached URL entry.
        """
        self.cache[url] = {
            "last_indexed_at": time.time(),
            "content_hash": content_hash,
            "collection_name": collection_name,
        }
        self._save()
