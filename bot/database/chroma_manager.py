from pathlib import Path

import chromadb

from config import CHROMA_COLLECTION_NAME, VECTOR_DB_PATH


class ChromaManager:
    """Manage ChromaDB client and collection lifecycle."""

    def __init__(
        self,
        persist_directory: str | Path = VECTOR_DB_PATH,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))

    def get_or_create_collection(self):
        """Return the configured ChromaDB collection."""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "PDF chunks for Web Knowledge Bot RAG"},
        )

    def reset_collection(self) -> None:
        """Delete and recreate the configured collection."""
        existing_names = [collection.name for collection in self.client.list_collections()]
        if self.collection_name in existing_names:
            self.client.delete_collection(self.collection_name)
        self.get_or_create_collection()

    def collection_exists(self) -> bool:
        """Return whether the configured collection exists."""
        return self.collection_name in [
            collection.name for collection in self.client.list_collections()
        ]

    def count_chunks(self) -> int:
        """Return the number of chunks in the configured collection."""
        return self.get_or_create_collection().count()
