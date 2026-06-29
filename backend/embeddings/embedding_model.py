"""
Embedding model factory for Google Gemini and HuggingFace embeddings.
"""

from __future__ import annotations

from typing import Any

import config
from utils.exceptions import EmbeddingError
from utils.logger import get_logger

logger = get_logger(__name__)

_model: Any | None = None
_provider: str | None = None


class AutoFallbackEmbeddings:
    """Embedding wrapper that falls back from Google to HuggingFace at runtime."""

    def __init__(self, primary: Any, fallback_factory) -> None:
        self.primary = primary
        self.fallback_factory = fallback_factory
        self.fallback: Any | None = None
        self.active_provider = "google"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            return self.primary.embed_documents(texts)
        except Exception as exc:
            logger.warning("Google embedding request failed; falling back to HuggingFace: %s", exc)
            self.active_provider = "huggingface"
            return self._fallback().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        try:
            return self.primary.embed_query(text)
        except Exception as exc:
            logger.warning("Google query embedding failed; falling back to HuggingFace: %s", exc)
            self.active_provider = "huggingface"
            return self._fallback().embed_query(text)

    def _fallback(self):
        if self.fallback is None:
            self.fallback = self.fallback_factory()
        return self.fallback


def _load_huggingface_embeddings():
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings

    logger.info("Loaded HuggingFace embedding model %s", config.HUGGINGFACE_EMBEDDING_MODEL)
    return HuggingFaceEmbeddings(model_name=config.HUGGINGFACE_EMBEDDING_MODEL)


def load_embedding_model(provider: str | None = None):
    """Return a cached LangChain-compatible embeddings object."""

    global _model, _provider
    requested = (provider or config.EMBEDDING_PROVIDER or "auto").lower()

    if _model is not None and (requested == "auto" or requested == _provider):
        return _model

    if requested in {"auto", "google"} and config.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            _model = GoogleGenerativeAIEmbeddings(
                model=config.GOOGLE_EMBEDDING_MODEL,
                google_api_key=config.GOOGLE_API_KEY,
            )
            _provider = "google"
            logger.info("Loaded Google embedding model %s", config.GOOGLE_EMBEDDING_MODEL)
            if requested == "auto":
                _model = AutoFallbackEmbeddings(_model, _load_huggingface_embeddings)
                _provider = "auto"
            return _model
        except Exception as exc:
            if requested == "google":
                raise EmbeddingError("Could not load Google embeddings.", provider="google") from exc
            logger.warning("Google embeddings unavailable; falling back to HuggingFace: %s", exc)

    if requested in {"auto", "huggingface"}:
        _model = _load_huggingface_embeddings()
        _provider = "huggingface"
        return _model

    raise EmbeddingError("No usable embedding provider configured.", provider=requested)


def get_embedding_provider() -> str:
    if _provider is None:
        load_embedding_model()
    return _provider or "unknown"


def generate_embeddings(chunks: list[str]) -> list[list[float]]:
    if not chunks:
        return []
    return load_embedding_model().embed_documents(chunks)


def generate_query_embedding(query: str) -> list[float]:
    return load_embedding_model().embed_query(query)
