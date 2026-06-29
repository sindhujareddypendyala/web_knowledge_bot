from api.schemas import SourceReference


class SourceAttributor:
    """Normalize source references returned with RAG answers."""

    def build_sources(
        self,
        sources: list[SourceReference],
        max_sources: int = 10,
    ) -> list[SourceReference]:
        """Deduplicate and score-sort source references."""
        unique_sources: dict[tuple[str, str | None, int | None, str | None], SourceReference] = {}

        for source in sources:
            key = (
                source.source_type.value,
                source.document_id or source.url,
                source.page_number,
                source.chunk_id,
            )

            existing = unique_sources.get(key)
            if existing is None or (source.score or 0.0) > (existing.score or 0.0):
                unique_sources[key] = source

        return sorted(
            unique_sources.values(),
            key=lambda source: source.score or 0.0,
            reverse=True,
        )[:max_sources]
