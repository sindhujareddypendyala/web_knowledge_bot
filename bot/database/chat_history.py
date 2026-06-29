import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from api.schemas import ChatMessageResponse, MessageRole, SourceReference
from config import SQLITE_DB_PATH


class ChatHistoryStore:
    """Persist chat messages and source references in SQLite."""

    def __init__(self, database_path: str | Path = SQLITE_DB_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def add_message(
        self,
        *,
        session_id: str,
        role: MessageRole,
        content: str,
        sources: list[SourceReference] | None = None,
    ) -> ChatMessageResponse:
        """Store one chat message and return the saved record."""
        message_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        normalized_sources = sources or []

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_messages (
                    id,
                    session_id,
                    role,
                    content,
                    sources_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role.value,
                    content,
                    self._serialize_sources(normalized_sources),
                    created_at.isoformat(),
                ),
            )

        return ChatMessageResponse(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            sources=normalized_sources,
            created_at=created_at,
        )

    def list_messages(
        self,
        *,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[ChatMessageResponse]:
        """Return recent chat messages, optionally limited to one session."""
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")

        query = """
            SELECT id, session_id, role, content, sources_json, created_at
            FROM chat_messages
        """
        params: list[object] = []

        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        messages = [self._row_to_message(row) for row in rows]
        return list(reversed(messages))

    def delete_session(self, session_id: str) -> int:
        """Delete all messages for a session and return deleted count."""
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,),
            )
            return cursor.rowcount

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
                ON chat_messages (session_id, created_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _serialize_sources(sources: list[SourceReference]) -> str:
        return json.dumps([source.model_dump(mode="json") for source in sources])

    @staticmethod
    def _deserialize_sources(raw_value: str) -> list[SourceReference]:
        try:
            values = json.loads(raw_value)
        except json.JSONDecodeError:
            return []

        return [SourceReference(**value) for value in values]

    def _row_to_message(self, row: sqlite3.Row) -> ChatMessageResponse:
        return ChatMessageResponse(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            role=MessageRole(str(row["role"])),
            content=str(row["content"]),
            sources=self._deserialize_sources(str(row["sources_json"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
