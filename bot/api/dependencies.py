from collections.abc import Callable
from functools import lru_cache
from typing import Any, TypeVar

from fastapi import HTTPException, Query, status

from config import Settings, settings


T = TypeVar("T")


class ServiceConfigurationError(RuntimeError):
    """Raised when a backend service cannot be constructed safely."""


def get_settings() -> Settings:
    """Return validated application settings for API endpoints."""
    settings.validate()
    settings.ensure_directories()
    return settings


def get_session_id(
    session_id: str | None = Query(default=None, max_length=128),
) -> str | None:
    """Normalize optional session IDs supplied through query parameters."""
    if session_id is None:
        return None

    cleaned = session_id.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="session_id cannot be blank.",
        )
    return cleaned


def _load_service(module_path: str, attribute_name: str) -> type[T]:
    """Import a service class only when an endpoint actually needs it."""
    try:
        module = __import__(module_path, fromlist=[attribute_name])
        service = getattr(module, attribute_name)
    except (ImportError, AttributeError) as exc:
        raise ServiceConfigurationError(
            f"{attribute_name} is not available in {module_path}."
        ) from exc

    return service


def _build_service(
    module_path: str,
    attribute_name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    service_class = _load_service(module_path, attribute_name)
    try:
        return service_class(*args, **kwargs)
    except Exception as exc:
        raise ServiceConfigurationError(
            f"Failed to initialize {attribute_name}: {exc}"
        ) from exc


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    """Return the Gemini embedding service used for document indexing."""
    app_settings = get_settings()
    return _build_service(
        "embeddings.embedding_model",
        "EmbeddingModel",
        api_key=app_settings.gemini_api_key,
        model_name=app_settings.embedding_model_name,
    )


@lru_cache(maxsize=1)
def get_vector_store() -> Any:
    """Return the ChromaDB-backed vector store service."""
    app_settings = get_settings()
    return _build_service(
        "embeddings.vector_store",
        "VectorStore",
        persist_directory=str(app_settings.vector_db_path),
        collection_name=app_settings.chroma_collection_name,
        embedding_model=get_embedding_model(),
    )


@lru_cache(maxsize=1)
def get_pdf_processor() -> Any:
    """Return the PDF processing service used during upload ingestion."""
    app_settings = get_settings()
    return _build_service(
        "pdf.pdf_processor",
        "PDFProcessor",
        upload_folder=app_settings.upload_folder,
        max_upload_size_bytes=app_settings.max_upload_size_bytes,
    )


@lru_cache(maxsize=1)
def get_pdf_retriever() -> Any:
    """Return the semantic PDF retriever service."""
    app_settings = get_settings()
    return _build_service(
        "embeddings.retriever",
        "PDFRetriever",
        vector_store=get_vector_store(),
        top_k=app_settings.top_k,
    )


@lru_cache(maxsize=1)
def get_gemini_service() -> Any:
    """Return the Gemini text generation service."""
    app_settings = get_settings()
    if not app_settings.gemini_api_key:
        raise ServiceConfigurationError("GEMINI_API_KEY is not configured.")

    return _build_service(
        "llm.gemini_service",
        "GeminiService",
        api_key=app_settings.gemini_api_key,
        model_name=app_settings.gemini_model_name,
    )


@lru_cache(maxsize=1)
def get_chat_history_store() -> Any:
    """Return the SQLite-backed chat history store."""
    app_settings = get_settings()
    return _build_service(
        "database.chat_history",
        "ChatHistoryStore",
        database_path=app_settings.sqlite_db_path,
    )


@lru_cache(maxsize=1)
def get_rag_pipeline() -> Any:
    """Return the complete PDF-first RAG pipeline."""
    return _build_service(
        "rag.rag_pipeline",
        "RAGPipeline",
        pdf_retriever=get_pdf_retriever(),
        gemini_service=get_gemini_service(),
        chat_history_store=get_chat_history_store(),
    )


def as_http_error(operation: str) -> Callable[[Exception], HTTPException]:
    """Convert service-layer exceptions into consistent API errors."""

    def converter(exc: Exception) -> HTTPException:
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if isinstance(exc, ServiceConfigurationError)
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return HTTPException(
            status_code=status_code,
            detail=f"{operation} failed: {exc}",
        )

    return converter
