"""
Retriever that queries and merges results from both PDF and website embeddings.
"""
from __future__ import annotations

from config import DEFAULT_COLLECTION_NAME
from embeddings.vector_store import WebsiteVectorStore
from models.chunk import RetrievedChunk
from utils.logger import get_logger

logger = get_logger(__name__)


class IntegratedRetriever:
    """
    Retrieves chunks from the vector database.
    Since both PDF and Website chunks coexist in the ChromaDB collection,
    a single query retrieves both. Can also query separate collections and merge.
    """

    def __init__(self, collection_name: str = DEFAULT_COLLECTION_NAME) -> None:
        self.collection_name = collection_name
        self.vector_store = WebsiteVectorStore(collection_name)

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        """
        Retrieve chunks matching the query from the vector store.
        Ranks the merged results by similarity score (confidence).
        """
        try:
            chunks = self.vector_store.retrieve(query, k=k)
            # RetrievedChunk computes confidence score as 1.0 / (1.0 + distance)
            # Sort by confidence descending
            chunks.sort(key=lambda c: c.confidence or 0.0, reverse=True)

            for index, chunk in enumerate(chunks, start=1):
                chunk.rank = index

            return chunks
        except Exception as exc:
            logger.error("Failed to retrieve chunks: %s", exc)
            return []

    def retrieve_merged(self, query: str, collections: list[str], k: int = 5) -> list[RetrievedChunk]:
        """
        Retrieve chunks from multiple collections, merge, deduplicate, and rank them by similarity.
        """
        all_chunks: list[RetrievedChunk] = []
        for coll in collections:
            try:
                store = WebsiteVectorStore(coll)
                chunks = store.retrieve(query, k=k)
                all_chunks.extend(chunks)
            except Exception as exc:
                logger.warning("Could not retrieve from collection %s: %s", coll, exc)

        # De-duplicate by chunk ID
        seen_ids = set()
        deduped_chunks = []
        for item in all_chunks:
            if item.chunk.chunk_id not in seen_ids:
                seen_ids.add(item.chunk.chunk_id)
                deduped_chunks.append(item)

        # Sort by confidence score descending
        deduped_chunks.sort(key=lambda c: c.confidence or 0.0, reverse=True)
        results = deduped_chunks[:k]

        for index, chunk in enumerate(results, start=1):
            chunk.rank = index

        return results
