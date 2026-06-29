"""
FastAPI dependencies for Website Knowledge services.
"""

from __future__ import annotations

from database.statistics import StatisticsService
from database.website_manager import WebsiteManager


def get_website_manager() -> WebsiteManager:
    return WebsiteManager()


def get_statistics_service() -> StatisticsService:
    return StatisticsService()
