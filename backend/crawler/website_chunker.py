"""
Recursive website document chunking.

Creates LangChain-compatible chunks with stable chunk IDs, website metadata,
and Chroma-safe metadata. Existing `create_chunks` and `chunk_documents`
helpers are preserved for the CLI pipeline.
"""

from __future__ import annotations

from typing import Any

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

from config import CHUNK_OVERLAP, CHUNK_SIZE
from models.chunk import WebsiteChunk
from models.document import WebsiteDocument
from utils.exceptions import ChunkingError
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:
        class Document:
            def __init__(self, page_content: str, metadata: dict | None = None) -> None:
                self.page_content = page_content
                self.metadata = metadata or {}


def _make_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    if chunk_overlap >= chunk_size:
        raise ChunkingError("chunk_overlap must be smaller than chunk_size.")
    if RecursiveCharacterTextSplitter is None:
        return SimpleTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )


class SimpleTextSplitter:
    """Small fallback splitter used when LangChain text splitters are absent."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        if not text:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return [chunk for chunk in chunks if chunk]


class WebsiteChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = _make_splitter(chunk_size, chunk_overlap)

    def chunk_text(self, text: str) -> list[str]:
        if not text:
            return []
        return self.splitter.split_text(text)

    def chunk_document(self, document: WebsiteDocument | dict[str, Any]) -> list[WebsiteChunk]:
        doc = document if isinstance(document, WebsiteDocument) else WebsiteDocument.from_dict(document)
        chunks: list[WebsiteChunk] = []

        cursor = 0
        for index, piece in enumerate(self.chunk_text(doc.text)):
            start = doc.text.find(piece[:50], cursor)
            if start < 0:
                start = cursor
            end = start + len(piece)
            cursor = max(end - self.chunk_overlap, end)
            chunks.append(
                WebsiteChunk.create(
                    website_id=doc.website_id or "default",
                    source_url=doc.source_url,
                    title=doc.title,
                    text=piece,
                    chunk_index=index,
                    start_char=start,
                    end_char=end,
                    metadata=doc.to_metadata(),
                )
            )
        return chunks

    def chunk_documents(self, documents: list[WebsiteDocument | dict[str, Any]]) -> list[WebsiteChunk]:
        chunks: list[WebsiteChunk] = []
        for document in documents:
            chunks.extend(self.chunk_document(document))
        logger.info("Chunked %s document(s) into %s chunk(s)", len(documents), len(chunks))
        return chunks

    def to_langchain_documents(self, documents: list[WebsiteDocument | dict[str, Any]]) -> list[Document]:
        return [chunk.to_langchain_document() for chunk in self.chunk_documents(documents)]


def create_chunks(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    return WebsiteChunker(chunk_size, chunk_overlap).chunk_text(text)


def chunk_documents(documents: list, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[Document]:
    return WebsiteChunker(chunk_size, chunk_overlap).to_langchain_documents(documents)
