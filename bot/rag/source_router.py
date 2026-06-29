from collections.abc import Callable

from api.schemas import SourceType
from embeddings.retriever import PDFRetriever, RetrievedChunk


WebsiteRetriever = Callable[[str, int], list[RetrievedChunk]]


class SourceRouter:
    """Route retrieval requests to PDF and future website retrievers."""

    def __init__(
        self,
        pdf_retriever: PDFRetriever,
        website_retriever: WebsiteRetriever | None = None,
    ) -> None:
        self.pdf_retriever = pdf_retriever
        self.website_retriever = website_retriever

    async def retrieve(
        self,
        *,
        query: str,
        source_types: list[SourceType],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Retrieve chunks from all requested knowledge sources."""
        retrieved_chunks: list[RetrievedChunk] = []

        if SourceType.PDF in source_types:
            retrieved_chunks.extend(
                await self.pdf_retriever.aretrieve(query=query, top_k=top_k)
            )

        if SourceType.WEBSITE in source_types and self.website_retriever is not None:
            retrieved_chunks.extend(self.website_retriever(query, top_k))

        return sorted(
            retrieved_chunks,
            key=lambda chunk: chunk.score,
            reverse=True,
        )[:top_k]
