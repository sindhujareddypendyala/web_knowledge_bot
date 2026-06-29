"""
Generic helper / utility functions shared across modules.
"""
import hashlib
import json
import os
from datetime import datetime


def generate_doc_id(text: str, url: str = "") -> str:
    """Deterministic short id for a chunk, based on its content + source URL."""
    raw = f"{url}:{text}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def save_json(data, path: str) -> None:
    """Writes `data` as pretty-printed JSON, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: str, default=None):
    """Reads JSON from `path`, returning `default` if the file doesn't exist."""
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def timestamp() -> str:
    """Current local time as a human-readable string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def truncate(text: str, max_chars: int = 200) -> str:
    """Shortens `text` to `max_chars`, appending '...' if it was cut."""
    text = text or ""
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def chunk_list(items: list, size: int):
    """Yields successive `size`-sized slices from `items`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]
