"""
Image extraction utilities for crawled HTML pages.

Purpose:
    Extracts useful image references, alt text, captions, dimensions, and lazy
    loading sources from documentation pages.

How it connects:
    Crawlers and parsers can attach extracted images to `WebsiteDocument`.
    Those image assets contribute to website statistics and can be exported as
    source metadata for another backend module when visual documentation
    context matters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from models.document import ExtractedAsset


SKIP_IMAGE_PREFIXES = ("data:image", "blob:")
SOURCE_ATTRIBUTES = ("src", "data-src", "data-original", "data-lazy-src", "data-url")


@dataclass(slots=True)
class ExtractedImage:
    """Structured image data extracted from one HTML page."""

    src: str
    alt: str = ""
    title: str = ""
    caption: str = ""
    width: str | None = None
    height: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_asset(self) -> ExtractedAsset:
        text = " ".join(part for part in (self.alt, self.title, self.caption) if part)
        return ExtractedAsset(
            kind="image",
            value=self.src,
            text=text,
            metadata={
                "alt": self.alt,
                "title": self.title,
                "caption": self.caption,
                "width": self.width,
                "height": self.height,
                **self.metadata,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return self.to_asset().to_dict()


class ImageExtractor:
    """Extract image assets from BeautifulSoup HTML documents."""

    def extract(self, soup: BeautifulSoup, source_url: str, limit: int = 100) -> list[ExtractedImage]:
        images: list[ExtractedImage] = []
        seen: set[str] = set()

        for tag in soup.find_all("img"):
            src = self._extract_src(tag, source_url)
            if not src or src in seen:
                continue

            seen.add(src)
            images.append(
                ExtractedImage(
                    src=src,
                    alt=_clean_space(tag.get("alt", "")),
                    title=_clean_space(tag.get("title", "")),
                    caption=self._extract_caption(tag),
                    width=tag.get("width"),
                    height=tag.get("height"),
                    metadata=self._extract_metadata(tag),
                )
            )

            if len(images) >= limit:
                break

        return images

    @staticmethod
    def _extract_src(tag: Tag, source_url: str) -> str | None:
        for attr in SOURCE_ATTRIBUTES:
            value = tag.get(attr)
            if not value:
                continue

            src = str(value).strip()
            if not src or src.startswith(SKIP_IMAGE_PREFIXES):
                continue
            return urljoin(source_url, src)

        srcset = tag.get("srcset")
        if srcset:
            first_candidate = str(srcset).split(",", 1)[0].strip().split(" ", 1)[0]
            if first_candidate and not first_candidate.startswith(SKIP_IMAGE_PREFIXES):
                return urljoin(source_url, first_candidate)

        return None

    @staticmethod
    def _extract_caption(tag: Tag) -> str:
        figure = tag.find_parent("figure")
        if not figure:
            return ""

        caption = figure.find("figcaption")
        if not caption:
            return ""
        return _clean_space(caption.get_text(" ", strip=True))

    @staticmethod
    def _extract_metadata(tag: Tag) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        for attr in ("class", "loading", "decoding", "aria-label"):
            value = tag.get(attr)
            if value:
                metadata[attr.replace("-", "_")] = value
        return metadata


def extract_images(soup: BeautifulSoup, source_url: str, limit: int = 100) -> list[ExtractedAsset]:
    """Convenience wrapper returning `ExtractedAsset` objects."""

    return [image.to_asset() for image in ImageExtractor().extract(soup, source_url, limit=limit)]


def _clean_space(value: str) -> str:
    return " ".join(str(value or "").split())
