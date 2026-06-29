"""
Website text processing utilities.

Purpose:
    Cleans raw extracted website content into high-signal, chunk-ready text by
    normalizing whitespace, removing boilerplate, preserving useful code/table
    context, and deduplicating repeated documentation fragments.

How it connects:
    Crawlers and parsers call `WebsiteProcessor.process_text()` before creating
    `WebsiteDocument` objects. Chunkers and vector stores then receive stable,
    clean content that improves embedding quality and retrieval precision.
"""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field

from utils.logger import get_logger

logger = get_logger(__name__)

NOISE_PATTERNS = (
    r"sponsor(?:ed)?\s*content",
    r"advertisement",
    r"subscribe to (?:our )?newsletter",
    r"accept (?:all )?cookies",
    r"cookie policy",
    r"privacy policy",
    r"terms of service",
    r"all rights reserved",
    r"skip to (?:main )?content",
    r"edit this page",
    r"was this page helpful\??",
    r"on this page",
    r"previous\s+next",
)

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_PATTERN = re.compile(r"[ \t\r\f\v]+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")


@dataclass(slots=True)
class ProcessedContent:
    """Result from processing extracted page content."""

    text: str
    original_length: int
    cleaned_length: int
    removed_noise_patterns: list[str] = field(default_factory=list)
    duplicate_sentences_removed: int = 0

    @property
    def compression_ratio(self) -> float:
        if self.original_length == 0:
            return 0.0
        return round(self.cleaned_length / self.original_length, 4)

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "original_length": self.original_length,
            "cleaned_length": self.cleaned_length,
            "removed_noise_patterns": self.removed_noise_patterns,
            "duplicate_sentences_removed": self.duplicate_sentences_removed,
            "compression_ratio": self.compression_ratio,
        }


class WebsiteProcessor:
    """Clean and normalize extracted website text."""

    def __init__(self, noise_patterns: tuple[str, ...] = NOISE_PATTERNS) -> None:
        self.noise_patterns = noise_patterns

    def process_text(
        self,
        text: str,
        *,
        code_blocks: list[str] | None = None,
        table_texts: list[str] | None = None,
        deduplicate: bool = True,
        append_tables: bool = False,
    ) -> ProcessedContent:
        original = text or ""
        cleaned = normalize_unicode(original)
        cleaned = html.unescape(cleaned)
        cleaned = remove_control_characters(cleaned)
        cleaned = normalize_line_breaks(cleaned)

        removed_patterns: list[str] = []
        for pattern in self.noise_patterns:
            updated = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
            if updated != cleaned:
                removed_patterns.append(pattern)
                cleaned = updated

        duplicates_removed = 0
        if deduplicate:
            cleaned, duplicates_removed = dedupe_sentences(cleaned)

        cleaned = remove_standalone_punctuation(cleaned)
        cleaned = remove_extra_spaces(cleaned)
        cleaned = append_context_blocks(
            cleaned,
            code_blocks=code_blocks,
            table_texts=table_texts if append_tables else None,
        )

        return ProcessedContent(
            text=cleaned,
            original_length=len(original),
            cleaned_length=len(cleaned),
            removed_noise_patterns=removed_patterns,
            duplicate_sentences_removed=duplicates_removed,
        )


def normalize_unicode(text: str) -> str:
    """Normalize Unicode into a stable, readable representation."""

    return unicodedata.normalize("NFKC", text or "")


def remove_control_characters(text: str) -> str:
    """Remove non-readable control characters while preserving newlines."""

    return CONTROL_CHAR_PATTERN.sub(" ", text or "")


def normalize_line_breaks(text: str) -> str:
    """Normalize line endings and collapse excessive blank lines."""

    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.strip() for line in normalized.splitlines())
    return MULTI_NEWLINE_PATTERN.sub("\n\n", normalized).strip()


def remove_extra_spaces(text: str) -> str:
    """Collapse whitespace while preserving paragraph-ish line breaks."""

    if not text:
        return ""

    lines = [WHITESPACE_PATTERN.sub(" ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return " ".join(lines).strip()


def remove_standalone_punctuation(text: str) -> str:
    """Remove punctuation fragments left behind after boilerplate stripping."""

    cleaned = re.sub(r"(^|\s)[.,;:!?]+(?=\s|$)", " ", text or "")
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def dedupe_sentences(text: str) -> tuple[str, int]:
    """Remove repeated sentences while preserving original order."""

    seen: set[str] = set()
    kept: list[str] = []
    duplicate_count = 0

    for sentence in SENTENCE_SPLIT_PATTERN.split(text or ""):
        stripped = sentence.strip()
        if not stripped:
            continue

        normalized = re.sub(r"\W+", "", stripped).lower()
        if normalized and normalized in seen:
            duplicate_count += 1
            continue

        if normalized:
            seen.add(normalized)
        kept.append(stripped)

    return " ".join(kept), duplicate_count


def remove_duplicates(text: str) -> str:
    """Legacy helper returning only deduplicated text."""

    deduped, _ = dedupe_sentences(text)
    return deduped


def append_context_blocks(
    text: str,
    *,
    code_blocks: list[str] | None = None,
    table_texts: list[str] | None = None,
) -> str:
    """Append useful extracted code/table context without duplicating content."""

    parts = [text] if text else []

    for block in code_blocks or []:
        cleaned_block = normalize_line_breaks(block)
        if cleaned_block and cleaned_block not in text:
            parts.append(f"Code block:\n{cleaned_block}")

    for table in table_texts or []:
        cleaned_table = normalize_line_breaks(table)
        if cleaned_table and cleaned_table not in text:
            parts.append(f"Table:\n{cleaned_table}")

    return "\n\n".join(parts).strip()


def clean_text(text: str) -> str:
    """Legacy helper: run the full text cleaning pipeline and return text."""

    return WebsiteProcessor().process_text(text).text
