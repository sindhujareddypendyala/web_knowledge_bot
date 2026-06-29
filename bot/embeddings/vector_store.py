from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from api.schemas import DocumentResponse
from config import CHROMA_COLLECTION_NAME, VECTOR_DB_PATH
from embeddings.embedding_model import EmbeddingModel
from pdf.pdf_metadata import PDFMetadataBuilder
from pdf.pdf_processor import ProcessedPDFDocument


@dataclass(frozen=True)
class SearchResult:
    """Semantic search result returned from the vector store."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class VectorStore:
    """ChromaDB-backed storage for embedded PDF chunks."""

    def __init__(
        self,
        persist_directory: str | Path = VECTOR_DB_PATH,
        collection_name: str = CHROMA_COLLECTION_NAME,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedding_model = embedding_model or EmbeddingModel()

        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "PDF chunks for Web Knowledge Bot RAG"},
        )

    def add_documents(
        self,
        documents: list[ProcessedPDFDocument],
    ) -> list[DocumentResponse]:
        """Embed and persist processed PDF documents in ChromaDB."""
        indexed_documents: list[DocumentResponse] = []

        for document in documents:
            if not document.chunks:
                continue

            ids = [chunk.id for chunk in document.chunks]
            texts = [chunk.text for chunk in document.chunks]
            embeddings = self.embedding_model.embed_documents(texts)
            metadatas = []

            for index, chunk in enumerate(document.chunks, start=1):
                metadatas.append(
                    PDFMetadataBuilder.chunk_metadata(
                        document_id=document.id,
                        document_name=document.filename,
                        page_number=chunk.page_number,
                        chunk_index=index,
                        page_count=document.page_count,
                        chunk_count=document.chunk_count,
                        uploaded_at=document.uploaded_at,
                        extra=chunk.metadata | document.metadata,
                    )
                )

            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            indexed_documents.append(PDFMetadataBuilder.from_processed_document(document))

        return indexed_documents

    def similarity_search(
        self,
        query: str,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return top matching chunks for a natural-language query."""
        query_embedding = self.embedding_model.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        search_results: list[SearchResult] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            score = max(0.0, 1.0 - float(distance))
            search_results.append(
                SearchResult(
                    id=chunk_id,
                    text=text or "",
                    metadata=dict(metadata or {}),
                    score=score,
                )
            )

        return search_results

    def list_documents(self) -> list[DocumentResponse]:
        """List unique PDF documents represented in the vector collection."""
        stored = self.collection.get(include=["metadatas"])
        document_map: dict[str, dict[str, Any]] = {}

        for metadata in stored.get("metadatas", []):
            if not metadata:
                continue

            document_id = str(metadata.get("document_id", ""))
            if not document_id or document_id in document_map:
                continue

            document_map[document_id] = dict(metadata)

        return [
            PDFMetadataBuilder.from_vector_metadata(metadata)
            for metadata in document_map.values()
        ]

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document from ChromaDB."""
        existing = self.collection.get(
            where={"document_id": document_id},
            include=["metadatas"],
        )
        ids = existing.get("ids", [])
        if not ids:
            return False

        self.collection.delete(where={"document_id": document_id})
        return True

    def count_chunks(self) -> int:
        """Return the number of stored chunks."""
        return self.collection.count()
