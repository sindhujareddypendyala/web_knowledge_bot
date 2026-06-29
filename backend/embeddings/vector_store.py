"""
ChromaDB-backed vector store for website chunks.
"""

from __future__ import annotations

from typing import Any

import config
from embeddings.embedding_model import load_embedding_model
from models.chunk import RetrievedChunk
from utils.exceptions import VectorStoreError
from utils.logger import get_logger
from utils.validators import is_valid_collection_name

logger = get_logger(__name__)

_stores: dict[str, object] = {}


def _load_chroma_class():
    try:
        from langchain_chroma import Chroma
        return Chroma
    except ImportError:
        try:
            from langchain_community.vectorstores import Chroma
            return Chroma
        except ImportError as exc:
            raise VectorStoreError(
                "Chroma vector-store dependencies are not installed. Run `pip install -r requirements.txt`.",
                collection_name=None,
            ) from exc


class WebsiteVectorStore:
    def __init__(self, collection_name: str = config.DEFAULT_COLLECTION_NAME) -> None:
        if not is_valid_collection_name(collection_name):
            raise VectorStoreError("Invalid ChromaDB collection name.", collection_name=collection_name)
        self.collection_name = collection_name
        self.embedding_model = load_embedding_model()

    def load(self):
        if self.collection_name not in _stores:
            Chroma = _load_chroma_class()
            _stores[self.collection_name] = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=config.VECTOR_DB_PATH,
            )
        return _stores[self.collection_name]

    def store_documents(self, documents: list[Any]):
        if not documents:
            return self.load()

        Chroma = _load_chroma_class()
        _stores[self.collection_name] = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            collection_name=self.collection_name,
            persist_directory=config.VECTOR_DB_PATH,
        )
        logger.info("Stored %s document chunk(s) in %s", len(documents), self.collection_name)
        return _stores[self.collection_name]

    def similarity_search(self, query: str, k: int = config.RETRIEVAL_TOP_K) -> list[Any]:
        return self.load().similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = config.RETRIEVAL_TOP_K, filter: dict | None = None) -> list[tuple[Any, float]]:
        return self.load().similarity_search_with_score(query, k=k, filter=filter)

    def retrieve(self, query: str, k: int = config.RETRIEVAL_TOP_K, filter: dict | None = None) -> list[RetrievedChunk]:
        pairs = self.similarity_search_with_score(query, k=k, filter=filter)
        return [
            RetrievedChunk.from_langchain_result(doc, rank=index + 1, distance=score)
            for index, (doc, score) in enumerate(pairs)
        ]

    def delete_collection(self) -> None:
        store = self.load()
        store.delete_collection()
        _stores.pop(self.collection_name, None)
        logger.info("Deleted Chroma collection %s", self.collection_name)


def store_embeddings(documents: list, collection_name: str = config.DEFAULT_COLLECTION_NAME):
    return WebsiteVectorStore(collection_name).store_documents(documents)


def load_embeddings(collection_name: str = config.DEFAULT_COLLECTION_NAME):
    return WebsiteVectorStore(collection_name).load()


def similarity_search(query: str, k: int = config.RETRIEVAL_TOP_K, collection_name: str = config.DEFAULT_COLLECTION_NAME) -> list:
    return WebsiteVectorStore(collection_name).similarity_search(query, k=k)


def similarity_search_with_score(
    query: str,
    k: int = config.RETRIEVAL_TOP_K,
    collection_name: str = config.DEFAULT_COLLECTION_NAME,
) -> list:
    return WebsiteVectorStore(collection_name).similarity_search_with_score(query, k=k)


def delete_collection(collection_name: str = config.DEFAULT_COLLECTION_NAME) -> None:
    WebsiteVectorStore(collection_name).delete_collection()
