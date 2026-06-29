"""
Small file-backed website cache with TTL.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from config import CACHE_TTL_SECONDS, TEMP_PATH


class CacheManager:
    def __init__(self, cache_dir: str | Path | None = None, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self.cache_dir = Path(cache_dir or Path(TEMP_PATH) / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def get(self, key: str, default: Any = None) -> Any:
        path = self._path(key)
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if self.ttl_seconds and time.time() - payload.get("created_at", 0) > self.ttl_seconds:
            return default
        return payload.get("value", default)

    def set(self, key: str, value: Any) -> None:
        with self._path(key).open("w", encoding="utf-8") as file:
            json.dump({"created_at": time.time(), "value": value}, file, indent=2, ensure_ascii=False)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"
