"""
Statistics helpers for indexed websites.
"""

from __future__ import annotations

from database.website_manager import WebsiteManager


class StatisticsService:
    def __init__(self, website_manager: WebsiteManager | None = None) -> None:
        self.website_manager = website_manager or WebsiteManager()

    def global_statistics(self) -> dict:
        records = self.website_manager.list()
        totals = {
            "websites": len(records),
            "ready_websites": sum(1 for record in records if record.status.value == "ready"),
            "pages_crawled": sum(record.statistics.pages_crawled for record in records),
            "chunks_indexed": sum(record.statistics.chunks_indexed for record in records),
            "images_extracted": sum(record.statistics.images_extracted for record in records),
            "tables_extracted": sum(record.statistics.tables_extracted for record in records),
            "broken_links": sum(record.statistics.broken_links for record in records),
        }
        return totals

    def website_statistics(self, website_id: str) -> dict:
        record = self.website_manager.get(website_id)
        return record.statistics.to_dict() | {"website_id": website_id}
