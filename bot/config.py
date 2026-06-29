import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc


def _get_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default

    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Centralized environment-backed configuration for the backend."""

    app_name: str = os.getenv("APP_NAME", "Web Knowledge Bot Backend")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").strip().lower() == "true"

    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model_name: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "models/gemini-embedding-001",
    )

    upload_folder: Path = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    vector_db_path: Path = BASE_DIR / os.getenv("VECTOR_DB_PATH", "vector_db")
    temp_folder: Path = BASE_DIR / os.getenv("TEMP_FOLDER", "temp")
    sqlite_db_path: Path = BASE_DIR / os.getenv(
        "SQLITE_DB_PATH",
        "database/chat_history.sqlite3",
    )

    chroma_collection_name: str = os.getenv(
        "CHROMA_COLLECTION_NAME",
        "web_knowledge_bot_pdf_chunks",
    )

    chunk_size: int = field(default_factory=lambda: _get_int("CHUNK_SIZE", 1000))
    chunk_overlap: int = field(default_factory=lambda: _get_int("CHUNK_OVERLAP", 200))
    top_k: int = field(default_factory=lambda: _get_int("TOP_K", 5))
    max_upload_size_mb: int = field(
        default_factory=lambda: _get_int("MAX_UPLOAD_SIZE_MB", 25),
    )

    cors_origins: list[str] = field(
        default_factory=lambda: _get_list("CORS_ORIGINS", ["*"]),
    )

    def validate(self) -> None:
        """Validate configuration values that can break runtime behavior."""
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be greater than 0.")

        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP cannot be negative.")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")

        if self.top_k <= 0:
            raise ValueError("TOP_K must be greater than 0.")

        if self.max_upload_size_mb <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be greater than 0.")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create filesystem directories required by the backend."""
        for directory in (
            self.upload_folder,
            self.vector_db_path,
            self.temp_folder,
            self.sqlite_db_path.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.validate()

# Backward-compatible constants used by existing modules.
GEMINI_API_KEY = settings.gemini_api_key
MODEL_NAME = settings.gemini_model_name
EMBEDDING_MODEL_NAME = settings.embedding_model_name

UPLOAD_FOLDER = str(settings.upload_folder)
VECTOR_DB_PATH = str(settings.vector_db_path)
TEMP_FOLDER = str(settings.temp_folder)
SQLITE_DB_PATH = str(settings.sqlite_db_path)

CHROMA_COLLECTION_NAME = settings.chroma_collection_name
CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
TOP_K = settings.top_k
MAX_UPLOAD_SIZE_MB = settings.max_upload_size_mb
MAX_UPLOAD_SIZE_BYTES = settings.max_upload_size_bytes
CORS_ORIGINS = settings.cors_origins
