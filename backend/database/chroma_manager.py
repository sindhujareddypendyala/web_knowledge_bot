"""
Low-level ChromaDB collection management.
"""

from __future__ import annotations

import config
from utils.exceptions import VectorStoreError
from utils.logger import get_logger
from utils.validators import is_valid_collection_name

logger = get_logger(__name__)

_client = None


def _load_chromadb():
    try:
        import chromadb
        return chromadb
    except ImportError as exc:
        raise VectorStoreError("ChromaDB is not installed. Run `pip install -r requirements.txt`.") from exc


def get_client():
    global _client
    if _client is None:
        chromadb = _load_chromadb()
        _client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
    return _client


def create_collection(name: str = config.DEFAULT_COLLECTION_NAME):
    if not is_valid_collection_name(name):
        raise VectorStoreError("Invalid ChromaDB collection name.", collection_name=name)
    collection = get_client().get_or_create_collection(name=name)
    logger.info("Collection %s ready with %s chunk(s)", name, collection.count())
    return collection


def get_collection(name: str = config.DEFAULT_COLLECTION_NAME):
    return get_client().get_collection(name=name)


def list_collections() -> list[str]:
    return [collection.name for collection in get_client().list_collections()]


def add_documents(collection, documents: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None, ids: list[str] | None = None):
    if not documents:
        return
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas or [{} for _ in documents],
        ids=ids or [f"doc_{index}" for index in range(len(documents))],
    )


def search(collection, query_embedding: list[float], top_k: int = config.RETRIEVAL_TOP_K):
    return collection.query(query_embeddings=[query_embedding], n_results=top_k)


def delete_collection(name: str = config.DEFAULT_COLLECTION_NAME) -> None:
    try:
        get_client().delete_collection(name=name)
        logger.info("Collection %s deleted", name)
    except Exception as exc:
        raise VectorStoreError("Failed to delete ChromaDB collection.", collection_name=name) from exc
