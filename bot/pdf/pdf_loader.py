import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_FOLDER


@dataclass(frozen=True)
class SavedPDF:
    """Metadata for a PDF saved to local storage."""

    document_id: str
    original_filename: str
    stored_filename: str
    file_path: Path
    size_bytes: int


class PDFLoader:
    """Validate and persist uploaded PDF files."""

    def __init__(
        self,
        upload_folder: str | Path = UPLOAD_FOLDER,
        max_upload_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    ) -> None:
        self.upload_folder = Path(upload_folder)
        self.max_upload_size_bytes = max_upload_size_bytes
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile) -> SavedPDF:
        """Save one uploaded PDF and return its storage metadata."""
        original_filename = self._validate_file(file)
        document_id = str(uuid.uuid4())
        stored_filename = f"{document_id}.pdf"
        file_path = self.upload_folder / stored_filename

        size_bytes = self._copy_upload(file, file_path)
        if size_bytes == 0:
            file_path.unlink(missing_ok=True)
            raise ValueError(f"{original_filename} is empty.")

        if size_bytes > self.max_upload_size_bytes:
            file_path.unlink(missing_ok=True)
            max_mb = self.max_upload_size_bytes // (1024 * 1024)
            raise ValueError(f"{original_filename} exceeds the {max_mb} MB upload limit.")

        return SavedPDF(
            document_id=document_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            size_bytes=size_bytes,
        )

    def _validate_file(self, file: UploadFile) -> str:
        filename = Path(file.filename or "").name.strip()
        if not filename:
            raise ValueError("Uploaded file must include a filename.")

        if Path(filename).suffix.lower() != ".pdf":
            raise ValueError(f"{filename} is not a PDF file.")

        if file.content_type not in {None, "", "application/pdf", "application/octet-stream", "binary/octet-stream"}:
            raise ValueError(f"{filename} must use application/pdf content type.")

        return filename

    @staticmethod
    def _copy_upload(file: UploadFile, destination: Path) -> int:
        file.file.seek(0)
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.seek(0)
        return destination.stat().st_size


def save_pdf(file: UploadFile) -> str:
    """Backward-compatible helper that saves a single PDF and returns its path."""
    saved_pdf = PDFLoader().save(file)
    return str(saved_pdf.file_path)
