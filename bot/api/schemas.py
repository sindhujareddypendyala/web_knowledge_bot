from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(str, Enum):
    """Knowledge source categories supported by the RAG pipeline."""

    PDF = "pdf"
    WEBSITE = "website"


class MessageRole(str, Enum):
    """Supported chat message roles for persisted conversation history."""

    USER = "user"
    ASSISTANT = "assistant"


class HealthResponse(BaseModel):
    """Health check payload returned by the backend."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["Web Knowledge Bot Backend"])
    version: str = Field(..., examples=["1.0.0"])
    timestamp: datetime


class UploadPDFResponse(BaseModel):
    """Response returned after one or more PDFs are processed."""

    success: bool
    message: str
    documents: list["DocumentResponse"] = Field(default_factory=list)
    failed_files: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """User question payload for the RAG chat endpoint."""

    question: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)
    source_types: list[SourceType] = Field(default_factory=lambda: [SourceType.PDF])
    top_k: int | None = Field(default=None, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Question cannot be empty.")
        return cleaned

    @field_validator("source_types")
    @classmethod
    def validate_source_types(cls, value: list[SourceType]) -> list[SourceType]:
        if not value:
            raise ValueError("At least one source type is required.")
        return value


class SourceReference(BaseModel):
    """Source details attached to generated answers."""

    source_type: SourceType
    document_id: str | None = None
    document_name: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    chunk_id: str | None = None
    url: str | None = None
    title: str | None = None
    score: float | None = Field(default=None, ge=0)
    snippet: str | None = None


class ChatResponse(BaseModel):
    """Generated answer returned by the RAG pipeline."""

    success: bool
    answer: str
    session_id: str
    sources: list[SourceReference] = Field(default_factory=list)
    found_answer: bool = True
    created_at: datetime


class DocumentStatus(str, Enum):
    """Lifecycle state for indexed documents."""

    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentResponse(BaseModel):
    """Metadata for an uploaded and indexed PDF document."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    source_type: SourceType = SourceType.PDF
    status: DocumentStatus
    page_count: int = Field(default=0, ge=0)
    chunk_count: int = Field(default=0, ge=0)
    uploaded_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentsResponse(BaseModel):
    """Collection response for indexed document listing."""

    success: bool
    documents: list[DocumentResponse] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class DeleteDocumentResponse(BaseModel):
    """Response returned after deleting an indexed document."""

    success: bool
    document_id: str
    message: str


class ChatMessageResponse(BaseModel):
    """Single message stored in chat history."""

    id: str
    session_id: str
    role: MessageRole
    content: str
    sources: list[SourceReference] = Field(default_factory=list)
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history returned for a session or all sessions."""

    success: bool
    session_id: str | None = None
    messages: list[ChatMessageResponse] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)


class ErrorResponse(BaseModel):
    """Standard error payload used across API endpoints."""

    success: bool = False
    error: str
    detail: str | None = None
