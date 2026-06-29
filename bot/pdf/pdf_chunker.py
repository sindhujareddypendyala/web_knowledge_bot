from langchain_text_splitters import RecursiveCharacterTextSplitter

from api.schemas import SourceType
from config import CHUNK_OVERLAP, CHUNK_SIZE
from pdf.pdf_processor import PDFChunk, PDFPageText


class PDFChunker:
    """Split extracted PDF page text into embedding-ready chunks."""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_pages(
        self,
        document_id: str,
        document_name: str,
        pages: list[PDFPageText],
    ) -> list[PDFChunk]:
        """Create chunks from page-level PDF text while preserving page metadata."""
        chunks: list[PDFChunk] = []

        for page in pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_chunks = self.splitter.split_text(page_text)
            for chunk_index, chunk_text in enumerate(page_chunks, start=1):
                cleaned_text = chunk_text.strip()
                if not cleaned_text:
                    continue

                chunk_id = f"{document_id}:page-{page.page_number}:chunk-{chunk_index}"
                chunks.append(
                    PDFChunk(
                        id=chunk_id,
                        document_id=document_id,
                        document_name=document_name,
                        page_number=page.page_number,
                        text=cleaned_text,
                        metadata={
                            "source_type": SourceType.PDF.value,
                            "document_id": document_id,
                            "document_name": document_name,
                            "page_number": page.page_number,
                            "chunk_index": chunk_index,
                        },
                    )
                )

        return chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Backward-compatible helper for splitting plain text."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]
