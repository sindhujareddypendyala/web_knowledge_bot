import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def new_id() -> str:
    """Return a random UUID string."""
    return str(uuid.uuid4())


def normalize_text(text: str) -> str:
    """Collapse repeated whitespace while preserving readable text."""
    return " ".join(text.split())


def make_snippet(text: str, max_length: int = 280) -> str:
    """Create a compact source snippet."""
    cleaned = normalize_text(text)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
