"""
Backend integration interface for exporting retrieved RAG context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from embeddings.hybrid_retriever import HybridRetriever


@dataclass(slots=True)
class BackendContextPackage:
    query: str
    website_id: str | None
    contexts: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "website_id": self.website_id,
            "contexts": self.contexts,
            "context_count": len(self.contexts),
        }


class BackendInterface:
    """Small boundary object used by another backend module."""

    def get_context(
        self,
        query: str,
        collection_name: str,
        website_id: str | None = None,
        k: int = 5,
    ) -> dict[str, Any]:
        contexts = HybridRetriever(collection_name).retrieve_context(query, k=k)
        return BackendContextPackage(query=query, website_id=website_id, contexts=contexts).to_dict()
