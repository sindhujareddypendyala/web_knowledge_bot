from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from api.dependencies import (
    as_http_error,
    get_chat_history_store,
    get_pdf_processor,
    get_rag_pipeline,
    get_session_id,
    get_settings,
    get_vector_store,
)
from api.schemas import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    DeleteDocumentResponse,
    DocumentsResponse,
    HealthResponse,
    UploadPDFResponse,
)
from config import Settings


router = APIRouter(tags=["Backend"])


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Return backend health and configuration readiness."""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/upload_pdf",
    response_model=UploadPDFResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
async def upload_pdf(
    files: list[UploadFile] = File(...),
    pdf_processor: Any = Depends(get_pdf_processor),
    vector_store: Any = Depends(get_vector_store),
) -> UploadPDFResponse:
    """Upload, process, chunk, embed, and index one or more PDF files."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one PDF file is required.",
        )

    try:
        documents = await pdf_processor.process_uploads(files)
        indexed_documents = vector_store.add_documents(documents)
    except Exception as exc:
        raise as_http_error("PDF upload")(exc) from exc

    return UploadPDFResponse(
        success=True,
        message=f"Indexed {len(indexed_documents)} PDF document(s).",
        documents=indexed_documents,
        failed_files=[],
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    rag_pipeline: Any = Depends(get_rag_pipeline),
) -> ChatResponse:
    """Answer a user question using retrieved indexed knowledge only."""
    try:
        result = await rag_pipeline.answer_question(
            question=request.question,
            session_id=request.session_id,
            source_types=request.source_types,
            top_k=request.top_k,
        )
    except Exception as exc:
        raise as_http_error("Chat response generation")(exc) from exc

    return result


@router.get("/documents", response_model=DocumentsResponse, tags=["Documents"])
async def list_documents(
    vector_store: Any = Depends(get_vector_store),
) -> DocumentsResponse:
    """List PDF documents indexed in the vector database."""
    try:
        documents = vector_store.list_documents()
    except Exception as exc:
        raise as_http_error("Document listing")(exc) from exc

    return DocumentsResponse(
        success=True,
        documents=documents,
        total=len(documents),
    )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteDocumentResponse,
    tags=["Documents"],
)
async def delete_document(
    document_id: str,
    vector_store: Any = Depends(get_vector_store),
) -> DeleteDocumentResponse:
    """Delete an indexed PDF document and its vector chunks."""
    cleaned_document_id = document_id.strip()
    if not cleaned_document_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="document_id cannot be blank.",
        )

    try:
        deleted = vector_store.delete_document(cleaned_document_id)
    except Exception as exc:
        raise as_http_error("Document deletion")(exc) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{cleaned_document_id}' was not found.",
        )

    return DeleteDocumentResponse(
        success=True,
        document_id=cleaned_document_id,
        message="Document deleted successfully.",
    )


@router.get("/history", response_model=ChatHistoryResponse, tags=["Chat"])
async def get_history(
    session_id: str | None = Depends(get_session_id),
    limit: int = Query(default=50, ge=1, le=200),
    chat_history_store: Any = Depends(get_chat_history_store),
) -> ChatHistoryResponse:
    """Return chat history for one session or recent messages across sessions."""
    try:
        messages = chat_history_store.list_messages(
            session_id=session_id,
            limit=limit,
        )
    except Exception as exc:
        raise as_http_error("Chat history retrieval")(exc) from exc

    return ChatHistoryResponse(
        success=True,
        session_id=session_id,
        messages=messages,
        total=len(messages),
    )
