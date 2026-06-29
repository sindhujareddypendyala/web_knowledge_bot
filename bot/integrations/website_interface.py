from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from api.schemas import SourceReference, SourceType
from embeddings.retriever import RetrievedChunk


@dataclass(frozen=True)
class WebsiteSearchResult:
    """Normalized website retrieval result accepted by the backend RAG pipeline."""

    text: str
    url: str
    title: str | None = None
    score: float = 0.0
    metadata: dict[str, Any] | None = None


WebsiteRetrieveFunction = Callable[[str, int], list[WebsiteSearchResult]]


class WebsiteRetrieverAdapter:
    """Adapt a future website retriever function into RAG-compatible chunks."""

    def __init__(self, retrieve_website: WebsiteRetrieveFunction) -> None:
        self.retrieve_website = retrieve_website

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Call the website retriever and normalize its results."""
        results = self.retrieve_website(query, top_k)
        chunks: list[RetrievedChunk] = []

        for index, result in enumerate(results, start=1):
            chunk_id = f"website:{index}:{abs(hash(result.url))}"
            metadata = {
                "source_type": SourceType.WEBSITE.value,
                "url": result.url,
                "title": result.title or result.url,
                **(result.metadata or {}),
            }
            source = SourceReference(
                source_type=SourceType.WEBSITE,
                url=result.url,
                title=result.title,
                chunk_id=chunk_id,
                score=result.score,
                snippet=_snippet(result.text),
            )

            chunks.append(
                RetrievedChunk(
                    id=chunk_id,
                    text=result.text,
                    score=result.score,
                    source=source,
                    metadata=metadata,
                )
            )

        return chunks


def build_website_retriever(
    retrieve_website: WebsiteRetrieveFunction | None,
) -> Callable[[str, int], list[RetrievedChunk]] | None:
    """Return a RAG-compatible website retriever when one is supplied."""
    if retrieve_website is None:
        return None

    adapter = WebsiteRetrieverAdapter(retrieve_website)
    return adapter.retrieve


def _snippet(text: str, max_length: int = 280) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."
