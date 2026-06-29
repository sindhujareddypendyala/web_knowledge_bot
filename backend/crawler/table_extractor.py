"""
Table extraction utilities for crawled HTML pages.

Purpose:
    Extracts HTML tables into structured rows and readable Markdown-like text
    so tabular documentation content can be indexed and exported cleanly.

How it connects:
    Crawlers and parsers can attach extracted tables to `WebsiteDocument`.
    The chunker can include table text in searchable context, statistics can
    count extracted tables, and backend integrations can preserve table source
    data for generated answers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup, Tag

from models.document import ExtractedAsset


@dataclass(slots=True)
class ExtractedTable:
    """Structured representation of one HTML table."""

    rows: list[list[str]]
    caption: str = ""
    headers: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return table_to_markdown(self.rows, caption=self.caption)

    def to_asset(self) -> ExtractedAsset:
        return ExtractedAsset(
            kind="table",
            value=self.caption or f"table:{len(self.rows)}x{self.column_count}",
            text=self.text,
            metadata={
                "caption": self.caption,
                "headers": self.headers,
                "row_count": len(self.rows),
                "column_count": self.column_count,
                **self.metadata,
            },
        )

    @property
    def column_count(self) -> int:
        return max((len(row) for row in self.rows), default=0)

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_asset().to_dict()
        payload["rows"] = self.rows
        return payload


class TableExtractor:
    """Extract and normalize HTML tables from BeautifulSoup documents."""

    def extract(self, soup: BeautifulSoup, limit: int = 50) -> list[ExtractedTable]:
        tables: list[ExtractedTable] = []

        for index, table in enumerate(soup.find_all("table")):
            rows = self._extract_rows(table)
            if not rows:
                continue

            caption = self._extract_caption(table)
            headers = self._extract_headers(table, rows)
            tables.append(
                ExtractedTable(
                    rows=rows,
                    caption=caption,
                    headers=headers,
                    metadata={"table_index": index},
                )
            )

            if len(tables) >= limit:
                break

        return tables

    @staticmethod
    def _extract_rows(table: Tag) -> list[list[str]]:
        rows: list[list[str]] = []

        for row in table.find_all("tr"):
            cells: list[str] = []
            for cell in row.find_all(["th", "td"], recursive=False):
                text = _clean_space(cell.get_text(" ", strip=True))
                colspan = _safe_int(cell.get("colspan"), default=1)
                cells.extend([text] * max(colspan, 1))

            if cells and any(cells):
                rows.append(cells)

        return rows

    @staticmethod
    def _extract_caption(table: Tag) -> str:
        caption = table.find("caption")
        return _clean_space(caption.get_text(" ", strip=True)) if caption else ""

    @staticmethod
    def _extract_headers(table: Tag, rows: list[list[str]]) -> list[str]:
        explicit_headers = [_clean_space(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
        if explicit_headers:
            return [header for header in explicit_headers if header]
        return rows[0] if rows else []


def extract_tables(soup: BeautifulSoup, limit: int = 50) -> list[ExtractedAsset]:
    """Convenience wrapper returning `ExtractedAsset` objects."""

    return [table.to_asset() for table in TableExtractor().extract(soup, limit=limit)]


def table_to_markdown(rows: list[list[str]], caption: str = "") -> str:
    """Convert table rows to compact Markdown-style text."""

    if not rows:
        return caption

    width = max(len(row) for row in rows)
    padded_rows = [row + [""] * (width - len(row)) for row in rows]
    lines: list[str] = []

    if caption:
        lines.append(caption)

    header = padded_rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * width) + " |")

    for row in padded_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def _clean_space(value: str) -> str:
    return " ".join(str(value or "").split())


def _safe_int(value: Any, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
