"""
HTML parsing utilities for the Website Knowledge Module.

Purpose:
    Converts raw HTML into structured, cleaned page data suitable for
    chunking, embedding, retrieval, and backend context export.

How it connects:
    Crawler modules call `HTMLParser.parse()` after fetching a page. The result
    feeds `WebsiteDocument`, while legacy helpers (`parse_html`, `extract_title`,
    `extract_main_content`) remain available for the existing CLI pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from crawler.metadata_extractor import PageMetadata, extract_metadata
from utils.exceptions import EmptyContentError, ParseError
from utils.logger import get_logger

logger = get_logger(__name__)

UNWANTED_TAGS = {
    "script",
    "style",
    "noscript",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
    "iframe",
    "svg",
    "button",
    "canvas",
}
CONTENT_SELECTORS = ("main", "article", "[role='main']", ".content", ".documentation", ".docs-content")


@dataclass(slots=True)
class ParsedHTML:
    """Structured output from parsing one HTML page."""

    source_url: str
    metadata: PageMetadata
    text: str
    code_blocks: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    raw_text_length: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_document_payload(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "url": self.source_url,
            "title": self.metadata.title,
            "text": self.text,
            "canonical_url": self.metadata.canonical_url,
            "description": self.metadata.description,
            "language": self.metadata.language,
            "headings": self.metadata.headings,
            "code_blocks": self.code_blocks,
            "links": self.links,
            "metadata": self.metadata.to_document_metadata() | self.extra,
        }


class HTMLParser:
    """Production parser for documentation-oriented HTML pages."""

    def parse(self, html: str, source_url: str) -> ParsedHTML:
        if not isinstance(html, str) or not html.strip():
            raise ParseError("Empty HTML content passed to parser.", url=source_url)

        soup = BeautifulSoup(html, "html.parser")
        metadata = extract_metadata(soup, source_url)
        code_blocks = self.extract_code_blocks(soup)
        links = self.extract_links(soup, source_url)

        cleaned_soup = remove_unwanted_tags(soup)
        text = self.extract_main_content(cleaned_soup)

        if not text:
            raise EmptyContentError(source_url)

        return ParsedHTML(
            source_url=source_url,
            metadata=metadata,
            text=text,
            code_blocks=code_blocks,
            links=links,
            raw_text_length=len(cleaned_soup.get_text(" ", strip=True)),
        )

    @staticmethod
    def extract_main_content(soup: BeautifulSoup) -> str:
        content_root = find_content_root(soup)
        text = content_root.get_text(separator=" ", strip=True)
        return clean_extracted_text(text)

    @staticmethod
    def extract_code_blocks(soup: BeautifulSoup, limit: int = 100) -> list[str]:
        blocks: list[str] = []
        for tag in soup.find_all(["pre", "code"]):
            text = tag.get_text("\n", strip=True)
            if text and text not in blocks:
                blocks.append(text)
            if len(blocks) >= limit:
                break
        return blocks

    @staticmethod
    def extract_links(soup: BeautifulSoup, source_url: str, limit: int = 500) -> list[str]:
        links: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue

            absolute_url = urljoin(source_url, href).split("#", 1)[0]
            if absolute_url and absolute_url not in seen:
                seen.add(absolute_url)
                links.append(absolute_url)
            if len(links) >= limit:
                break
        return links


def remove_unwanted_tags(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove non-content tags in-place and return the same soup."""

    for tag in soup.find_all(UNWANTED_TAGS):
        tag.decompose()
    return soup


def find_content_root(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    """Find the most likely readable content root for documentation pages."""

    for selector in CONTENT_SELECTORS:
        candidate = soup.select_one(selector)
        if candidate and candidate.get_text(strip=True):
            return candidate

    return soup.find("body") or soup


def clean_extracted_text(text: str) -> str:
    """Normalize whitespace in extracted text."""

    return " ".join((text or "").split())


def parse_html(html: str) -> BeautifulSoup:
    """Legacy helper: parse raw HTML and remove unwanted tags."""

    if not html:
        raise ValueError("Empty HTML content passed to parse_html()")
    return remove_unwanted_tags(BeautifulSoup(html, "html.parser"))


def remove_scripts(soup: BeautifulSoup) -> BeautifulSoup:
    """Legacy helper kept for existing crawler imports."""

    return remove_unwanted_tags(soup)


def extract_title(soup: BeautifulSoup) -> str:
    """Legacy helper: extract a page title from a soup tree."""

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return clean_extracted_text(title)

    h1 = soup.find("h1")
    if h1:
        return clean_extracted_text(h1.get_text(" ", strip=True))

    return "Untitled Page"


def extract_main_content(soup: BeautifulSoup) -> str:
    """Legacy helper: extract main readable text from a soup tree."""

    return HTMLParser.extract_main_content(soup)


def parse_page(html: str, source_url: str) -> ParsedHTML:
    """Convenience wrapper for parsing one HTML page."""

    return HTMLParser().parse(html, source_url)
