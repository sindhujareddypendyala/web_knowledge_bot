"""
File-backed indexed website registry.
"""

from __future__ import annotations

import json
from pathlib import Path

from config import WEBSITE_DOCS_PATH
from models.website import WebsiteRecord, create_website_record
from utils.exceptions import DuplicateWebsiteError, WebsiteNotFoundError
from utils.logger import get_logger
from utils.validators import normalize_url

logger = get_logger(__name__)


class WebsiteManager:
    def __init__(self, registry_path: str | Path | None = None) -> None:
        self.registry_path = Path(registry_path or Path(WEBSITE_DOCS_PATH) / "websites.json")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, url: str, allow_existing: bool = True) -> WebsiteRecord:
        normalized = normalize_url(url)
        existing = self.find_by_url(normalized)
        if existing:
            if allow_existing:
                return existing
            raise DuplicateWebsiteError(normalized, existing.website_id)

        record = create_website_record(base_url=url, normalized_url=normalized)
        records = self._load()
        records[record.website_id] = record.to_dict()
        self._save(records)
        return record

    def save(self, record: WebsiteRecord) -> WebsiteRecord:
        records = self._load()
        records[record.website_id] = record.to_dict()
        self._save(records)
        return record

    def get(self, website_id: str) -> WebsiteRecord:
        payload = self._load().get(website_id)
        if not payload:
            raise WebsiteNotFoundError(website_id)
        return WebsiteRecord.from_dict(payload)

    def list(self) -> list[WebsiteRecord]:
        return [WebsiteRecord.from_dict(payload) for payload in self._load().values()]

    def find_by_url(self, url: str) -> WebsiteRecord | None:
        normalized = normalize_url(url)
        for record in self.list():
            if record.normalized_url == normalized:
                return record
        return None

    def delete(self, website_id: str) -> WebsiteRecord:
        records = self._load()
        payload = records.pop(website_id, None)
        if not payload:
            raise WebsiteNotFoundError(website_id)
        self._save(records)
        return WebsiteRecord.from_dict(payload)

    def _load(self) -> dict:
        if not self.registry_path.exists():
            return {}
        with self.registry_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self, records: dict) -> None:
        with self.registry_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)


default_website_manager = WebsiteManager()
