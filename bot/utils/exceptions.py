class WebKnowledgeBotError(Exception):
    """Base exception for backend domain errors."""


class ConfigurationError(WebKnowledgeBotError):
    """Raised when required configuration is missing or invalid."""


class PDFProcessingError(WebKnowledgeBotError):
    """Raised when a PDF cannot be saved, read, or chunked."""


class VectorStoreError(WebKnowledgeBotError):
    """Raised when vector database operations fail."""


class RetrievalError(WebKnowledgeBotError):
    """Raised when semantic retrieval fails."""


class LLMGenerationError(WebKnowledgeBotError):
    """Raised when Gemini response generation fails."""


class ChatHistoryError(WebKnowledgeBotError):
    """Raised when chat history persistence fails."""
