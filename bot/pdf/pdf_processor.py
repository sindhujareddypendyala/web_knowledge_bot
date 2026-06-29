import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from pypdf import PdfReader

from api.schemas import DocumentStatus, SourceType
from config import CHUNK_OVERLAP, CHUNK_SIZE, MAX_UPLOAD_SIZE_BYTES, UPLOAD_FOLDER
from pdf.pdf_loader import PDFLoader, SavedPDF


@dataclass(frozen=True)
class PDFPageText:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


@dataclass(frozen=True)
class PDFChunk:
    """Chunk of PDF text ready for embedding and vector storage."""

    id: str
    document_id: str
    document_name: str
    page_number: int
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ProcessedPDFDocument:
    """Fully processed PDF document produced by the ingestion pipeline."""

    id: str
    filename: str
    file_path: Path
    source_type: SourceType
    status: DocumentStatus
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    pages: list[PDFPageText]
    chunks: list[PDFChunk]
    metadata: dict[str, Any] = field(default_factory=dict)


class PDFProcessor:
    """Extract text and chunks from uploaded PDF files."""

    def __init__(
        self,
        upload_folder: str | Path = UPLOAD_FOLDER,
        max_upload_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        loader: PDFLoader | None = None,
    ) -> None:
        self.loader = loader or PDFLoader(
            upload_folder=upload_folder,
            max_upload_size_bytes=max_upload_size_bytes,
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def process_uploads(
        self,
        files: list[UploadFile],
    ) -> list[ProcessedPDFDocument]:
        """Process multiple uploaded PDFs into indexed document payloads."""
        processed_documents: list[ProcessedPDFDocument] = []
        loop = asyncio.get_event_loop()

        for file in files:
            doc = await loop.run_in_executor(None, self.process_upload, file)
            processed_documents.append(doc)

        return processed_documents

    def process_upload(self, file: UploadFile) -> ProcessedPDFDocument:
        """Save, extract, and chunk a single uploaded PDF."""
        saved_pdf = self.loader.save(file)
        pages = self.extract_pages(saved_pdf.file_path)

        if not any(page.text.strip() for page in pages):
            saved_pdf.file_path.unlink(missing_ok=True)
            raise ValueError(f"{saved_pdf.original_filename} contains no extractable text.")

        chunks = self.chunk_pages(
            document_id=saved_pdf.document_id,
            document_name=saved_pdf.original_filename,
            pages=pages,
        )

        uploaded_at = datetime.now(timezone.utc)
        return ProcessedPDFDocument(
            id=saved_pdf.document_id,
            filename=saved_pdf.original_filename,
            file_path=saved_pdf.file_path,
            source_type=SourceType.PDF,
            status=DocumentStatus.INDEXED,
            page_count=len(pages),
            chunk_count=len(chunks),
            uploaded_at=uploaded_at,
            pages=pages,
            chunks=chunks,
            metadata={
                "stored_filename": saved_pdf.stored_filename,
                "size_bytes": saved_pdf.size_bytes,
                "uploaded_at": uploaded_at.isoformat(),
            },
        )

    @staticmethod
    def extract_pages(pdf_path: str | Path) -> list[PDFPageText]:
        """Extract text from each page in a PDF."""
        try:
            reader = PdfReader(str(pdf_path))
        except Exception as exc:
            raise ValueError(f"Unable to read PDF file: {exc}") from exc

        pages: list[PDFPageText] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            pages.append(
                PDFPageText(
                    page_number=index,
                    text=_normalize_text(text),
                )
            )

        return pages

    def chunk_pages(
        self,
        document_id: str,
        document_name: str,
        pages: list[PDFPageText],
    ) -> list[PDFChunk]:
        """Chunk PDF pages with the dedicated chunker when available."""
        try:
            from pdf.pdf_chunker import PDFChunker

            return PDFChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            ).chunk_pages(
                document_id=document_id,
                document_name=document_name,
                pages=pages,
            )
        except (ImportError, AttributeError):
            return self._fallback_chunk_pages(document_id, document_name, pages)

    def _fallback_chunk_pages(
        self,
        document_id: str,
        document_name: str,
        pages: list[PDFPageText],
    ) -> list[PDFChunk]:
        chunks: list[PDFChunk] = []

        for page in pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            start = 0
            chunk_index = 1
            while start < len(page_text):
                end = min(start + self.chunk_size, len(page_text))
                text = page_text[start:end].strip()
                if text:
                    chunk_id = f"{document_id}:page-{page.page_number}:chunk-{chunk_index}"
                    chunks.append(
                        PDFChunk(
                            id=chunk_id,
                            document_id=document_id,
                            document_name=document_name,
                            page_number=page.page_number,
                            text=text,
                            metadata={
                                "source_type": SourceType.PDF.value,
                                "document_id": document_id,
                                "document_name": document_name,
                                "page_number": page.page_number,
                                "chunk_index": chunk_index,
                            },
                        )
                    )

                if end >= len(page_text):
                    break

                start = max(end - self.chunk_overlap, start + 1)
                chunk_index += 1

        return chunks


def extract_text_from_pdf(pdf_path: str) -> str:
    """Backward-compatible helper that returns all extractable PDF text."""
    pages = PDFProcessor.extract_pages(pdf_path)
    return "\n".join(page.text for page in pages if page.text).strip()


def _normalize_text(text: str) -> str:
    return "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()
