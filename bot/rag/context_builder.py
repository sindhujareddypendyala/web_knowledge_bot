from dataclasses import dataclass

from api.schemas import SourceReference
from embeddings.retriever import RetrievedChunk
from llm.prompts import format_context_block


@dataclass(frozen=True)
class BuiltContext:
    """Prompt context plus source references used for attribution."""

    context: str
    sources: list[SourceReference]


class ContextBuilder:
    """Build labeled context blocks from retrieved chunks."""

    def build(self, chunks: list[RetrievedChunk]) -> BuiltContext:
        """Create a prompt context string and aligned source list."""
        context_blocks: list[str] = []
        sources: list[SourceReference] = []

        for index, chunk in enumerate(chunks, start=1):
            label = f"S{index}"
            source = chunk.source.model_copy(update={"title": label})
            sources.append(source)

            context_blocks.append(
                format_context_block(
                    source_label=label,
                    text=chunk.text,
                    document_name=source.document_name,
                    page_number=source.page_number,
                    url=source.url,
                )
            )

        return BuiltContext(
            context="\n\n".join(context_blocks),
            sources=sources,
        )
