from dataclasses import dataclass
from typing import Any

from api.schemas import SourceReference, SourceType
from config import TOP_K
from embeddings.vector_store import SearchResult, VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    """PDF chunk returned by semantic retrieval."""

    id: str
    text: str
    score: float
    source: SourceReference
    metadata: dict[str, Any]


class PDFRetriever:
    """Retrieve relevant PDF chunks for a user query."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        top_k: int = TOP_K,
        min_score: float = 0.0,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k
        self.min_score = min_score

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant PDF chunks for a query."""
        cleaned_query = " ".join(query.split())
        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        requested_top_k = top_k or self.top_k
        results = self.vector_store.similarity_search(
            query=cleaned_query,
            top_k=requested_top_k,
            where={"source_type": SourceType.PDF.value},
        )

        return [
            self._to_retrieved_chunk(result)
            for result in results
            if result.score >= self.min_score
        ]

    async def aretrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Async-compatible retrieval wrapper for FastAPI pipelines."""
        return self.retrieve(query=query, top_k=top_k)

    @staticmethod
    def _to_retrieved_chunk(result: SearchResult) -> RetrievedChunk:
        metadata = result.metadata
        source = SourceReference(
            source_type=SourceType.PDF,
            document_id=_optional_str(metadata.get("document_id")),
            document_name=_optional_str(metadata.get("document_name")),
            page_number=_optional_int(metadata.get("page_number")),
            chunk_id=result.id,
            score=result.score,
            snippet=_snippet(result.text),
        )

        return RetrievedChunk(
            id=result.id,
            text=result.text,
            score=result.score,
            source=source,
            metadata=metadata,
        )


def retrieve_pdf(query: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
    """Backward-compatible helper for retrieving PDF chunks directly."""
    return PDFRetriever(top_k=top_k).retrieve(query)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _snippet(text: str, max_length: int = 280) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."
