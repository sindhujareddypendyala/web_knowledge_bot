"""
Pydantic schemas for the Website Knowledge Module API.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=25, ge=1, le=500)
    max_depth: int = Field(default=3, ge=0, le=10)


class IndexRequest(CrawlRequest):
    refresh: bool = False


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    website_id: str | None = None
    collection_name: str | None = None
    k: int = Field(default=5, ge=1, le=50)
    mode: Literal["vector", "hybrid"] = "hybrid"


class RefreshRequest(BaseModel):
    website_id: str
    max_pages: int = Field(default=25, ge=1, le=500)
    max_depth: int = Field(default=3, ge=0, le=10)


class CrawlResponse(BaseModel):
    website_id: str
    url: str
    pages_crawled: int
    failed_urls: list[str]
    documents: list[dict[str, Any]]


class IndexResponse(BaseModel):
    website_id: str
    collection_name: str
    pages_crawled: int
    chunks_indexed: int
    status: str


class RetrieveResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
    result_count: int


class WebsiteResponse(BaseModel):
    websites: list[dict[str, Any]]


class StatisticsResponse(BaseModel):
    statistics: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
