"""
High-level retrieval interface for Website Knowledge RAG.
"""

from __future__ import annotations

import config
from embeddings.vector_store import WebsiteVectorStore
from models.chunk import RetrievedChunk
from utils.exceptions import RetrievalError
from utils.logger import get_logger
from utils.validators import validate_query, validate_positive_int

logger = get_logger(__name__)


class WebsiteRetriever:
    def __init__(self, collection_name: str = config.DEFAULT_COLLECTION_NAME) -> None:
        self.collection_name = collection_name
        self.vector_store = WebsiteVectorStore(collection_name)

    def retrieve(self, query: str, k: int = config.RETRIEVAL_TOP_K) -> list[RetrievedChunk]:
        normalized_query = validate_query(query)
        validate_positive_int(k, "k", minimum=1, maximum=50)
        try:
            results = self.vector_store.retrieve(normalized_query, k=k)
            logger.info("Retrieved %s chunk(s) for query", len(results))
            return results
        except RetrievalError:
            raise
        except Exception as exc:
            error = RetrievalError("Failed to retrieve relevant website chunks.", query=normalized_query)
            error.details["reason"] = str(exc)
            error.details["collection_name"] = self.collection_name
            raise error from exc

    def retrieve_context(self, query: str, k: int = config.RETRIEVAL_TOP_K) -> list[dict]:
        return [chunk.to_context_dict() for chunk in self.retrieve(query, k=k)]


def retrieve(query: str, k: int = config.RETRIEVAL_TOP_K, collection_name: str = config.DEFAULT_COLLECTION_NAME) -> list[dict]:
    return WebsiteRetriever(collection_name).retrieve_context(query, k=k)


def retrieve_with_scores(
    query: str,
    k: int = config.RETRIEVAL_TOP_K,
    collection_name: str = config.DEFAULT_COLLECTION_NAME,
) -> list[dict]:
    return [item.to_dict() for item in WebsiteRetriever(collection_name).retrieve(query, k=k)]
