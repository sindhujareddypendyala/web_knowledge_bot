from collections.abc import Sequence

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import EMBEDDING_MODEL_NAME, GEMINI_API_KEY


class EmbeddingModel:
    """Google Generative AI embedding wrapper used by the vector store."""

    def __init__(
        self,
        api_key: str | None = GEMINI_API_KEY,
        model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for embedding generation.")

        self.model_name = model_name
        self._client = GoogleGenerativeAIEmbeddings(
            model=model_name,
            api_key=api_key,
        )

    @property
    def client(self) -> GoogleGenerativeAIEmbeddings:
        """Return the underlying LangChain embeddings client."""
        return self._client

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of document chunks."""
        cleaned_texts = self._clean_texts(texts)
        if not cleaned_texts:
            return []

        return self._client.embed_documents(cleaned_texts)

    def embed_query(self, query: str) -> list[float]:
        """Embed a user query for semantic search."""
        cleaned_query = " ".join(query.split())
        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        return self._client.embed_query(cleaned_query)

    async def aembed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Asynchronously embed a batch of document chunks when supported."""
        cleaned_texts = self._clean_texts(texts)
        if not cleaned_texts:
            return []

        return await self._client.aembed_documents(cleaned_texts)

    async def aembed_query(self, query: str) -> list[float]:
        """Asynchronously embed a user query when supported."""
        cleaned_query = " ".join(query.split())
        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        return await self._client.aembed_query(cleaned_query)

    @staticmethod
    def _clean_texts(texts: Sequence[str]) -> list[str]:
        return [" ".join(text.split()) for text in texts if text and text.strip()]


def get_embedding_model() -> EmbeddingModel:
    """Backward-compatible factory for modules that need embeddings directly."""
    return EmbeddingModel()
