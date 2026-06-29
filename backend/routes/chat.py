"""
FastAPI router for grounded RAG chat based on automatic website retrieval.
"""
from __future__ import annotations

import time
import logging
from typing import List, Optional
import io
import pypdf
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

import config
from services.domain_classifier import DomainClassifier
from services.website_search import search_trusted_pages
from services.website_crawler import AsyncWebsiteCrawler
from services.website_cache import WebsiteCache
from crawler.website_chunker import WebsiteChunker
from vector_store.vector_store import RAGVectorStore
from retrievers.website_retriever import IntegratedRetriever
from database.chat_history import create_session, add_message, get_history
from database.website_manager import WebsiteManager
from api.dependencies import get_website_manager
from models.website import WebsiteStatus
from services.trusted_sites import get_trusted_prefixes
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user query or question.")
    session_id: Optional[str] = Field(None, description="Optional active chat session ID.")


class ChatSource(BaseModel):
    title: str = Field(..., description="Page title.")
    url: str = Field(..., description="Source URL.")
    confidence: float = Field(..., description="Similarity confidence score.")
    rank: int = Field(..., description="Result rank.")
    source_type: str = Field("website", description="Content source type (website or pdf).")


class ChatResponse(BaseModel):
    session_id: str = Field(..., description="Active session ID.")
    response: str = Field(..., description="Gemini generated and source-grounded response.")
    sources: List[ChatSource] = Field(default_factory=list, description="Retrieved sources used for answering.")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    website_manager: WebsiteManager = Depends(get_website_manager),
) -> ChatResponse:
    """
    Automatic Domain-Specific Retrieval Chat Endpoint.
    1. Detects domain key.
    2. Searches trusted documentation sites.
    3. Crawls & indexes new/expired pages asynchronously.
    4. Retrieves context chunks from both PDF & website vector store.
    5. Generates grounded response using Gemini.
    """
    start_time = time.time()

    # 1. Manage Chat Session & History
    session_id = request.session_id or create_session()
    add_message(session_id, "user", request.message)

    # 2. Classify Domain from User Question
    classifier = DomainClassifier()
    domain_key = classifier.classify(request.message)

    sources: List[ChatSource] = []
    retrieved_chunks = []

    if domain_key:
        logger.info("Detected technical domain: %s for query: '%s'", domain_key, request.message)

        # 3. Retrieve Trusted Website Prefixes & Search Relevant Pages
        prefixes = get_trusted_prefixes(domain_key)
        if prefixes:
            urls = await search_trusted_pages(request.message, domain_key, k=3)
            logger.info("Discovered top documentation pages: %s", urls)

            # 4. Check Cache and Crawl Missing/Expired URLs
            cache = WebsiteCache()
            urls_to_crawl = [url for url in urls if not cache.is_cached_and_valid(url)]

            if urls_to_crawl:
                logger.info("Crawling %d new/expired pages: %s", len(urls_to_crawl), urls_to_crawl)
                crawler = AsyncWebsiteCrawler()
                documents = await crawler.crawl_pages(urls_to_crawl, website_id=domain_key)

                if documents:
                    # Chunk documents
                    chunker = WebsiteChunker()
                    chunks = chunker.chunk_documents(documents)

                    # Instantiate Website record to track indexing state in registry
                    base_url = prefixes[0]
                    record = website_manager.create(base_url)
                    record.mark_status(WebsiteStatus.INDEXING)
                    website_manager.save(record)

                    # Store chunks in unified vector store
                    vector_store = RAGVectorStore()
                    vector_store.store_website_chunks(chunks, website_name=domain_key)

                    # Save index status and statistics
                    record.statistics.pages_crawled += len(documents)
                    record.statistics.chunks_indexed += len(chunks)
                    record.mark_status(WebsiteStatus.READY)
                    website_manager.save(record)

                    # Update cache entries
                    for doc in documents:
                        cache.update(
                            url=doc.source_url,
                            content_hash=doc.content_hash or "",
                            collection_name=vector_store.collection_name,
                        )
                    logger.info("Successfully indexed %d chunks for domain %s", len(chunks), domain_key)
            else:
                logger.info("All discovered pages are fresh in cache. Skipping crawling.")

        # 5. Retrieve Context (combining PDF and Web)
        retriever = IntegratedRetriever()
        retrieved_chunks = retriever.retrieve(request.message, k=5)
    else:
        logger.info("No technical domain detected. Returning domain-specific fallback response.")
        fallback_response = (
            "I am a domain-specific technical documentation assistant. "
            "I can only assist with queries related to my supported domains: "
            "Python, FastAPI, Docker, Kubernetes, React, AWS, Linux, Git, and PostgreSQL. "
            "Please ask a question related to one of these topics."
        )
        add_message(session_id, "assistant", fallback_response)
        return ChatResponse(
            session_id=session_id,
            response=fallback_response,
            sources=[],
        )

    # Map retrieved chunks to response sources schema
    for chunk in retrieved_chunks:
        meta = chunk.chunk.metadata
        sources.append(
            ChatSource(
                title=chunk.title,
                url=chunk.source_url,
                confidence=chunk.confidence or 0.0,
                rank=chunk.rank,
                source_type=meta.get("source_type", "website"),
            )
        )

    # 6. Build RAG Prompt with Context & Chat History
    context_text = ""
    for idx, c in enumerate(retrieved_chunks, start=1):
        context_text += f"[{idx}] Source: {c.title} ({c.source_url})\nContent: {c.text}\n\n"

    history = get_history(session_id)
    # Get last 5 message pairs (excluding the user query that was just appended)
    history_context = ""
    for msg in history[-6:-1]:
        history_context += f"{msg['role'].capitalize()}: {msg['content']}\n"

    prompt = f"""You are a helpful, source-grounded RAG chatbot. Answer the user's question using only the provided context.
If the context does not contain the answer, say "I cannot find the answer in the provided documentation" or answer based on your knowledge but clearly state that it is not in the provided documentation.
Always cite the source number (e.g. [1], [2]) when referencing facts from the context.

Context:
{context_text}

Chat History:
{history_context}

Question: {request.message}
Answer:"""

    # 7. Generate Response using Gemini (with automatic Groq fallback if the key is a Groq key)
    response_text = ""
    api_key = config.GOOGLE_API_KEY
    try:
        if api_key and api_key.startswith("gsk_"):
            logger.info("Detected Groq API key in GOOGLE_API_KEY. Utilizing Groq API client fallback.")
            from groq import Groq
            client = Groq(api_key=api_key)
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.0,
                )
                response_text = chat_completion.choices[0].message.content
            except Exception:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="llama3-8b-8192",
                    temperature=0.0,
                )
                response_text = chat_completion.choices[0].message.content
        else:
            llm = ChatGoogleGenerativeAI(
                model=config.GOOGLE_CHAT_MODEL,
                google_api_key=api_key,
                temperature=0.0,
            )
            res = await llm.ainvoke([HumanMessage(content=prompt)])
            response_text = str(res.content)
    except Exception as exc:
        logger.error("LLM API generation failed: %s", exc)
        response_text = (
            f"I retrieved relevant documentation but failed to generate a response. "
            f"Please verify your API key configuration. (Error: {exc})"
        )

    # 8. Save Assistant Response in History
    add_message(session_id, "assistant", response_text)

    latency = time.time() - start_time
    logger.info(
        "Chat request processed in %.4fs. Domain: %s, Sources: %d",
        latency,
        domain_key,
        len(sources),
    )

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        sources=sources,
    )


class UploadPDFResponse(BaseModel):
    success: bool
    message: str
    documents: list[str]


@router.post("/upload_pdf", response_model=UploadPDFResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadPDFResponse:
    """
    Upload and index a PDF file in the vector store.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        file_bytes = await file.read()
        pdf_file = io.BytesIO(file_bytes)
        
        reader = pypdf.PdfReader(pdf_file)
        text_content = ""
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="The uploaded PDF file is empty or has no extractable text.")
            
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        vector_store = RAGVectorStore()
        vector_store.store_pdf_chunks(chunks, pdf_name=file.filename)
        
        return UploadPDFResponse(
            success=True,
            message=f"Successfully indexed {len(chunks)} chunks from PDF document '{file.filename}'.",
            documents=[file.filename]
        )
    except Exception as exc:
        logger.error("Failed to parse/index PDF: %s", exc)
        raise HTTPException(status_code=500, detail=f"PDF indexing failed: {exc}")
