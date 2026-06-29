from pathlib import Path

from config import MAX_UPLOAD_SIZE_BYTES
from database.session_manager import SessionManager


def validate_pdf_filename(filename: str | None) -> str:
    """Validate and normalize an uploaded PDF filename."""
    cleaned = Path(filename or "").name.strip()
    if not cleaned:
        raise ValueError("Uploaded file must include a filename.")

    if Path(cleaned).suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are allowed.")

    return cleaned


def validate_upload_size(size_bytes: int, limit_bytes: int = MAX_UPLOAD_SIZE_BYTES) -> None:
    """Validate an uploaded file size."""
    if size_bytes <= 0:
        raise ValueError("Uploaded file is empty.")

    if size_bytes > limit_bytes:
        limit_mb = limit_bytes // (1024 * 1024)
        raise ValueError(f"Uploaded file exceeds the {limit_mb} MB limit.")


def validate_question(question: str) -> str:
    """Normalize and validate a user question."""
    cleaned = " ".join(question.split())
    if not cleaned:
        raise ValueError("Question cannot be empty.")
    return cleaned


def validate_session_id(session_id: str | None) -> str | None:
    """Validate an optional session ID."""
    if session_id is None:
        return None

    cleaned = session_id.strip()
    if not SessionManager.is_valid_session_id(cleaned):
        raise ValueError("Invalid session_id format.")

    return cleaned
