import uuid
from datetime import datetime, timezone
from typing import Any

from api.schemas import ChatResponse, MessageRole, SourceType
from embeddings.retriever import PDFRetriever
from llm.gemini_service import GeminiService
from llm.prompts import NO_ANSWER_MESSAGE
from llm.response_generator import ResponseGenerator
from rag.context_builder import ContextBuilder
from rag.source_attribution import SourceAttributor
from rag.source_router import SourceRouter, WebsiteRetriever


class RAGPipeline:
    """Coordinate retrieval, context construction, generation, and persistence."""

    def __init__(
        self,
        pdf_retriever: PDFRetriever,
        gemini_service: GeminiService,
        chat_history_store: Any | None = None,
        website_retriever: WebsiteRetriever | None = None,
        context_builder: ContextBuilder | None = None,
        source_attributor: SourceAttributor | None = None,
    ) -> None:
        self.source_router = SourceRouter(
            pdf_retriever=pdf_retriever,
            website_retriever=website_retriever,
        )
        self.response_generator = ResponseGenerator(gemini_service=gemini_service)
        self.context_builder = context_builder or ContextBuilder()
        self.source_attributor = source_attributor or SourceAttributor()
        self.chat_history_store = chat_history_store

    async def answer_question(
        self,
        *,
        question: str,
        session_id: str | None = None,
        source_types: list[SourceType] | None = None,
        top_k: int | None = None,
    ) -> ChatResponse:
        """Answer a user question using retrieved indexed knowledge only."""
        cleaned_question = " ".join(question.split())
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        resolved_session_id = session_id or str(uuid.uuid4())
        requested_sources = source_types or [SourceType.PDF]
        requested_top_k = top_k or 5

        retrieved_chunks = await self.source_router.retrieve(
            query=cleaned_question,
            source_types=requested_sources,
            top_k=requested_top_k,
        )
        built_context = self.context_builder.build(retrieved_chunks)
        generated = await self.response_generator.generate_answer(
            question=cleaned_question,
            context=built_context.context,
        )

        sources = (
            self.source_attributor.build_sources(built_context.sources)
            if generated.found_answer
            else []
        )

        response = ChatResponse(
            success=True,
            answer=generated.answer or NO_ANSWER_MESSAGE,
            session_id=resolved_session_id,
            sources=sources,
            found_answer=generated.found_answer,
            created_at=datetime.now(timezone.utc),
        )

        self._persist_chat_turn(
            session_id=resolved_session_id,
            question=cleaned_question,
            response=response,
        )
        return response

    def _persist_chat_turn(
        self,
        *,
        session_id: str,
        question: str,
        response: ChatResponse,
    ) -> None:
        if self.chat_history_store is None:
            return

        self.chat_history_store.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=question,
            sources=[],
        )
        self.chat_history_store.add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response.answer,
            sources=response.sources,
        )
