from dataclasses import dataclass

from llm.gemini_service import GeminiService
from llm.prompts import NO_ANSWER_MESSAGE, OUT_OF_DOMAIN_MESSAGE, build_rag_prompt


TECHNICAL_DOMAIN_TERMS = {
    "api",
    "authentication",
    "authorization",
    "backend",
    "bug",
    "cli",
    "cloud",
    "code",
    "command",
    "config",
    "configuration",
    "cybersecurity",
    "database",
    "debug",
    "deploy",
    "developer",
    "documentation",
    "endpoint",
    "error",
    "framework",
    "function",
    "guide",
    "install",
    "integration",
    "library",
    "manual",
    "module",
    "package",
    "parameter",
    "protocol",
    "reference",
    "request",
    "response",
    "sdk",
    "security",
    "server",
    "service",
    "software",
    "system",
    "technical",
    "tool",
    "troubleshoot",
    "version",
}


@dataclass(frozen=True)
class GeneratedResponse:
    """Answer text and grounding status produced by the LLM layer."""

    answer: str
    found_answer: bool


class ResponseGenerator:
    """Generate grounded answers from retrieved RAG context."""

    def __init__(
        self,
        gemini_service: GeminiService | None = None,
    ) -> None:
        self.gemini_service = gemini_service or GeminiService()
        self.prompt = build_rag_prompt()

    async def generate_answer(
        self,
        *,
        question: str,
        context: str,
    ) -> GeneratedResponse:
        """Generate an answer using only supplied retrieval context."""
        cleaned_question = " ".join(question.split())
        cleaned_context = context.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        if not cleaned_context:
            return GeneratedResponse(
                answer=NO_ANSWER_MESSAGE,
                found_answer=False,
            )

        if not _is_technical_documentation_query(cleaned_question, cleaned_context):
            return GeneratedResponse(
                answer=OUT_OF_DOMAIN_MESSAGE,
                found_answer=False,
            )

        messages = self.prompt.format_messages(
            question=cleaned_question,
            context=cleaned_context,
        )
        answer = await self.gemini_service.agenerate(messages)
        normalized_answer = answer.strip() or NO_ANSWER_MESSAGE
        found_answer = (
            NO_ANSWER_MESSAGE not in normalized_answer
            and OUT_OF_DOMAIN_MESSAGE not in normalized_answer
        )

        return GeneratedResponse(
            answer=normalized_answer,
            found_answer=found_answer,
        )

    def generate_answer_sync(
        self,
        *,
        question: str,
        context: str,
    ) -> GeneratedResponse:
        """Synchronous answer generation for scripts and tests."""
        cleaned_question = " ".join(question.split())
        cleaned_context = context.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        if not cleaned_context:
            return GeneratedResponse(
                answer=NO_ANSWER_MESSAGE,
                found_answer=False,
            )

        if not _is_technical_documentation_query(cleaned_question, cleaned_context):
            return GeneratedResponse(
                answer=OUT_OF_DOMAIN_MESSAGE,
                found_answer=False,
            )

        messages = self.prompt.format_messages(
            question=cleaned_question,
            context=cleaned_context,
        )
        answer = self.gemini_service.generate(messages)
        normalized_answer = answer.strip() or NO_ANSWER_MESSAGE
        found_answer = (
            NO_ANSWER_MESSAGE not in normalized_answer
            and OUT_OF_DOMAIN_MESSAGE not in normalized_answer
        )

        return GeneratedResponse(
            answer=normalized_answer,
            found_answer=found_answer,
        )


def _is_technical_documentation_query(question: str, context: str) -> bool:
    combined_text = f"{question} {context}".lower()
    return any(term in combined_text for term in TECHNICAL_DOMAIN_TERMS)
