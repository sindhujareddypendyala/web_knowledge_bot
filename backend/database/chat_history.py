"""
Lightweight, file-backed chat history store so the RAG chatbot can keep
track of prior turns in a session (and they survive an app restart).
Each session is saved as its own JSON file under chat_history/.
"""
import json
import os
import uuid
from datetime import datetime, timezone

import config
from utils.logger import get_logger

logger = get_logger(__name__)

HISTORY_DIR = os.path.join(config.BASE_DIR, "chat_history")
os.makedirs(HISTORY_DIR, exist_ok=True)


def _history_path(session_id: str) -> str:
    return os.path.join(HISTORY_DIR, f"{session_id}.json")


def _save_history(session_id: str, history: list) -> None:
    with open(_history_path(session_id), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def create_session() -> str:
    """Starts a new chat session and returns its id."""
    session_id = str(uuid.uuid4())
    _save_history(session_id, [])
    logger.info(f"Created new chat session: {session_id}")
    return session_id


def add_message(session_id: str, role: str, content: str) -> list:
    """Appends a {role, content, timestamp} message and persists it. Returns full history."""
    history = get_history(session_id)
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save_history(session_id, history)
    return history


def get_history(session_id: str) -> list:
    """Returns the full message history for a session (empty list if none yet)."""
    path = _history_path(session_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_history(session_id: str) -> None:
    """Wipes a session's history (keeps the session id valid)."""
    _save_history(session_id, [])
    logger.info(f"Cleared chat history for session: {session_id}")


def delete_session(session_id: str) -> None:
    """Removes a session's history file entirely."""
    path = _history_path(session_id)
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Deleted chat session: {session_id}")
