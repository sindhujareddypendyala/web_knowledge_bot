from typing import Any

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_API_KEY, MODEL_NAME


class GeminiService:
    """Google Gemini chat model wrapper for grounded RAG answers."""

    def __init__(
        self,
        api_key: str | None = GEMINI_API_KEY,
        model_name: str = MODEL_NAME,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        request_timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini response generation.")

        self.model_name = model_name
        self._client = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=request_timeout,
        )

    @property
    def client(self) -> ChatGoogleGenerativeAI:
        """Return the underlying LangChain chat model."""
        return self._client

    def generate(self, messages: list[BaseMessage] | str) -> str:
        """Generate a response from Gemini."""
        response = self._client.invoke(messages)
        return self._extract_text(response)

    async def agenerate(self, messages: list[BaseMessage] | str) -> str:
        """Generate a response from Gemini asynchronously."""
        response = await self._client.ainvoke(messages)
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: Any) -> str:
        content = getattr(response, "content", response)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
            return "\n".join(parts).strip()

        return str(content).strip()


def get_gemini_service() -> GeminiService:
    """Backward-compatible factory for direct Gemini access."""
    return GeminiService()
