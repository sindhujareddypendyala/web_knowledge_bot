from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.schemas import DocumentResponse, DocumentStatus, SourceType
from pdf.pdf_processor import ProcessedPDFDocument


class PDFMetadataBuilder:
    """Build normalized metadata payloads for processed PDF documents."""

    @staticmethod
    def from_processed_document(document: ProcessedPDFDocument) -> DocumentResponse:
        """Convert an internal processed PDF object into an API document response."""
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            source_type=document.source_type,
            status=document.status,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
            uploaded_at=document.uploaded_at,
            metadata=PDFMetadataBuilder.clean_metadata(document.metadata),
        )

    @staticmethod
    def from_vector_metadata(metadata: dict[str, Any]) -> DocumentResponse:
        """Build an API document response from metadata stored in ChromaDB."""
        uploaded_at = PDFMetadataBuilder.parse_datetime(metadata.get("uploaded_at"))

        return DocumentResponse(
            id=str(metadata["document_id"]),
            filename=str(metadata.get("document_name", "unknown.pdf")),
            source_type=SourceType.PDF,
            status=DocumentStatus.INDEXED,
            page_count=int(metadata.get("page_count", 0)),
            chunk_count=int(metadata.get("chunk_count", 0)),
            uploaded_at=uploaded_at,
            metadata=PDFMetadataBuilder.clean_metadata(metadata),
        )

    @staticmethod
    def chunk_metadata(
        *,
        document_id: str,
        document_name: str,
        page_number: int,
        chunk_index: int,
        page_count: int,
        chunk_count: int,
        uploaded_at: datetime,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create Chroma-compatible metadata for a PDF chunk."""
        metadata: dict[str, Any] = {
            "source_type": SourceType.PDF.value,
            "document_id": document_id,
            "document_name": document_name,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "page_count": page_count,
            "chunk_count": chunk_count,
            "uploaded_at": uploaded_at.isoformat(),
        }

        if extra:
            metadata.update(PDFMetadataBuilder.clean_metadata(extra))

        return metadata

    @staticmethod
    def clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        """Return metadata values that are safe for JSON and vector-store storage."""
        cleaned: dict[str, Any] = {}

        for key, value in metadata.items():
            if value is None:
                continue

            if isinstance(value, Path):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            else:
                cleaned[key] = str(value)

        return cleaned

    @staticmethod
    def parse_datetime(value: Any) -> datetime:
        """Parse stored datetime metadata with a UTC fallback."""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass

        return datetime.now(timezone.utc)
