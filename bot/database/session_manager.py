import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


@dataclass(frozen=True)
class ChatSession:
    """Runtime chat session metadata."""

    id: str
    created_at: datetime


class SessionManager:
    """Create and validate chat session identifiers."""

    def create_session(self) -> ChatSession:
        """Create a new chat session."""
        return ChatSession(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
        )

    def resolve_session_id(self, session_id: str | None) -> str:
        """Return an existing valid session ID or create a new one."""
        if session_id is None:
            return self.create_session().id

        cleaned = session_id.strip()
        if not self.is_valid_session_id(cleaned):
            raise ValueError("Invalid session_id format.")

        return cleaned

    @staticmethod
    def is_valid_session_id(session_id: str) -> bool:
        """Validate session ID format."""
        return bool(SESSION_ID_PATTERN.fullmatch(session_id))
