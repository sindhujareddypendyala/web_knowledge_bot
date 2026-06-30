"""
Vector store interface ensuring coexistence of PDF and Website embeddings in ChromaDB.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from config import DEFAULT_COLLECTION_NAME
from embeddings.vector_store import WebsiteVectorStore


class RAGVectorStore:
    """
    Handles indexing of document chunks into ChromaDB.
    Enforces standardized metadata for both PDF and website content.
    """

    def __init__(self, collection_name: str = DEFAULT_COLLECTION_NAME) -> None:
        self.collection_name = collection_name
        self.store = WebsiteVectorStore(collection_name)

    def store_website_chunks(self, chunks: list[Any], website_name: str) -> None:
        """
        Store WebsiteChunk objects into the vector store.
        Injects the required metadata keys for source attribution and retrieval filters.
        """
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

        documents = []
        for chunk in chunks:
            # Obtain base metadata
            meta = chunk.to_metadata()

            # Enforce the required metadata keys
            meta["source_type"] = "website"
            meta["website_name"] = website_name
            meta["page_title"] = chunk.title
            meta["url"] = chunk.source_url
            meta["timestamp"] = datetime.now(timezone.utc).isoformat()

            documents.append(Document(page_content=chunk.text, metadata=meta))

        self.store.store_documents(documents)

    def store_pdf_chunks(self, chunks: list[Any], pdf_name: str) -> None:
        """
        Store PDF chunks into the vector store (for future integration).
        Injects the required metadata keys for source attribution.
        """
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

        documents = []
        for chunk in chunks:
            is_str = isinstance(chunk, str)
            meta = {} if is_str else (getattr(chunk, "metadata", {}) or {})
            meta["source_type"] = "pdf"
            meta["pdf_name"] = pdf_name
            meta["page_title"] = pdf_name if is_str else getattr(chunk, "title", pdf_name)
            meta["title"] = pdf_name if is_str else getattr(chunk, "title", pdf_name)
            meta["url"] = pdf_name if is_str else getattr(chunk, "source_url", pdf_name)
            meta["source_url"] = pdf_name if is_str else getattr(chunk, "source_url", pdf_name)
            meta["timestamp"] = datetime.now(timezone.utc).isoformat()

            page_content = chunk if is_str else getattr(chunk, "text", getattr(chunk, "page_content", str(chunk)))
            documents.append(Document(page_content=page_content, metadata=meta))

        self.store.store_documents(documents)
