"""
Metadata extraction for crawled HTML pages.

Purpose:
    Extracts page-level metadata such as title, description, canonical URL,
    language, headings, Open Graph fields, and common documentation signals.

How it connects:
    The HTML parser and crawler use `MetadataExtractor` after fetching a page.
    Extracted metadata is attached to `WebsiteDocument`, persisted in ChromaDB
    through chunk metadata, returned by retrieval APIs, and included in backend
    context exports for better source attribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(slots=True)
class PageMetadata:
    """Structured metadata extracted from one HTML page."""

    source_url: str
    title: str = "Untitled"
    description: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    headings: list[str] = field(default_factory=list)
    meta_keywords: list[str] = field(default_factory=list)
    open_graph: dict[str, str] = field(default_factory=dict)
    twitter: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "title": self.title,
            "description": self.description,
            "canonical_url": self.canonical_url,
            "language": self.language,
            "headings": self.headings,
            "meta_keywords": self.meta_keywords,
            "open_graph": self.open_graph,
            "twitter": self.twitter,
            "extra": self.extra,
        }

    def to_document_metadata(self) -> dict[str, Any]:
        """Return metadata fields commonly attached to documents/chunks."""

        return {
            "source_url": self.source_url,
            "title": self.title,
            "description": self.description,
            "canonical_url": self.canonical_url,
            "language": self.language,
            "headings": self.headings,
            "meta_keywords": self.meta_keywords,
            **self.extra,
        }


class MetadataExtractor:
    """Extract useful metadata from BeautifulSoup HTML documents."""

    def extract(self, soup: BeautifulSoup, source_url: str) -> PageMetadata:
        title = self.extract_title(soup)
        description = self.extract_description(soup)
        canonical_url = self.extract_canonical_url(soup, source_url)
        language = self.extract_language(soup)

        return PageMetadata(
            source_url=source_url,
            title=title,
            description=description,
            canonical_url=canonical_url,
            language=language,
            headings=self.extract_headings(soup),
            meta_keywords=self.extract_keywords(soup),
            open_graph=self.extract_prefixed_meta(soup, "og:"),
            twitter=self.extract_prefixed_meta(soup, "twitter:"),
            extra=self.extract_extra(soup),
        )

    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        candidates = [
            _meta_content(soup, property_name="og:title"),
            _meta_content(soup, name="twitter:title"),
            soup.title.get_text(" ", strip=True) if soup.title else "",
        ]

        for candidate in candidates:
            if candidate:
                return _clean_space(candidate)
        return "Untitled"

    @staticmethod
    def extract_description(soup: BeautifulSoup) -> str | None:
        for candidate in (
            _meta_content(soup, name="description"),
            _meta_content(soup, property_name="og:description"),
            _meta_content(soup, name="twitter:description"),
        ):
            if candidate:
                return _clean_space(candidate)
        return None

    @staticmethod
    def extract_canonical_url(soup: BeautifulSoup, source_url: str) -> str | None:
        canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
        href = canonical.get("href") if canonical else None
        if not href:
            og_url = _meta_content(soup, property_name="og:url")
            href = og_url or None
        return urljoin(source_url, href.strip()) if href else None

    @staticmethod
    def extract_language(soup: BeautifulSoup) -> str | None:
        html = soup.find("html")
        language = html.get("lang") if html else None
        if not language:
            language = _meta_content(soup, http_equiv="content-language")
        return language.strip().lower() if language else None

    @staticmethod
    def extract_headings(soup: BeautifulSoup, limit: int = 30) -> list[str]:
        headings: list[str] = []
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = _clean_space(tag.get_text(" ", strip=True))
            if text and text not in headings:
                headings.append(text)
            if len(headings) >= limit:
                break
        return headings

    @staticmethod
    def extract_keywords(soup: BeautifulSoup) -> list[str]:
        keywords = _meta_content(soup, name="keywords")
        if not keywords:
            return []
        return [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]

    @staticmethod
    def extract_prefixed_meta(soup: BeautifulSoup, prefix: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if not key or not content or not key.startswith(prefix):
                continue
            values[key.removeprefix(prefix)] = _clean_space(content)
        return values

    @staticmethod
    def extract_extra(soup: BeautifulSoup) -> dict[str, Any]:
        generator = _meta_content(soup, name="generator")
        docs_version = (
            _meta_content(soup, name="version")
            or _meta_content(soup, name="docsearch:version")
            or _meta_content(soup, property_name="article:tag")
        )

        extra: dict[str, Any] = {}
        if generator:
            extra["generator"] = _clean_space(generator)
        if docs_version:
            extra["docs_version"] = _clean_space(docs_version)
        return extra


def extract_metadata(soup: BeautifulSoup, source_url: str) -> PageMetadata:
    """Convenience wrapper for simple callers."""

    return MetadataExtractor().extract(soup, source_url)


def _meta_content(
    soup: BeautifulSoup,
    *,
    name: str | None = None,
    property_name: str | None = None,
    http_equiv: str | None = None,
) -> str | None:
    attrs: dict[str, str] = {}
    if name:
        attrs["name"] = name
    if property_name:
        attrs["property"] = property_name
    if http_equiv:
        attrs["http-equiv"] = http_equiv

    tag = soup.find("meta", attrs=attrs)
    content = tag.get("content") if tag else None
    return content.strip() if content else None


def _clean_space(value: str) -> str:
    return " ".join(value.split())
