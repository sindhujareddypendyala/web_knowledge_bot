from langchain_core.prompts import ChatPromptTemplate


NO_ANSWER_MESSAGE = (
    "I could not find this answer in the indexed knowledge. "
    "Please upload or index a source that contains the relevant information."
)

OUT_OF_DOMAIN_MESSAGE = (
    "I can only answer questions about indexed technical documentation. "
    "Please ask about APIs, software, cybersecurity, code, systems, tools, or technical manuals."
)


SYSTEM_PROMPT = """You are Web Knowledge Bot, a careful technical documentation RAG assistant.

Rules:
- Answer only technical documentation questions about APIs, software, cybersecurity, code, systems, tools, developer guides, manuals, or technical reference material.
- If the question is not about technical documentation, say exactly:
  "{out_of_domain_message}"
- Answer using only the provided context.
- Do not use outside knowledge or make assumptions.
- If the context does not contain the answer, say exactly:
  "{no_answer_message}"
- Keep the answer technically precise and concise.
- When useful, mention source labels such as [S1], [S2], or page numbers.
- Do not invent file names, page numbers, URLs, code, commands, or citations.
"""


USER_PROMPT = """Context:
{context}

Question:
{question}

Answer:"""


def build_rag_prompt() -> ChatPromptTemplate:
    """Create the prompt template used for grounded RAG answers."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]
    ).partial(
        no_answer_message=NO_ANSWER_MESSAGE,
        out_of_domain_message=OUT_OF_DOMAIN_MESSAGE,
    )


def format_context_block(
    *,
    source_label: str,
    text: str,
    document_name: str | None = None,
    page_number: int | None = None,
    url: str | None = None,
) -> str:
    """Format one retrieved source chunk for the RAG prompt."""
    location_parts = []
    if document_name:
        location_parts.append(f"document={document_name}")
    if page_number:
        location_parts.append(f"page={page_number}")
    if url:
        location_parts.append(f"url={url}")

    location = ", ".join(location_parts) if location_parts else "source=unknown"
    cleaned_text = " ".join(text.split())
    return f"[{source_label}] {location}\n{cleaned_text}"
