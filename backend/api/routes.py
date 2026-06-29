"""
FastAPI routes for crawling, indexing, retrieval, and website management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import (
    CrawlRequest,
    CrawlResponse,
    IndexRequest,
    IndexResponse,
    RefreshRequest,
    RetrieveRequest,
    RetrieveResponse,
    StatisticsResponse,
    WebsiteResponse,
)
from api.dependencies import get_statistics_service, get_website_manager
from crawler.async_crawler import AsyncWebsiteCrawler
from crawler.website_chunker import WebsiteChunker
from database.statistics import StatisticsService
from database.website_manager import WebsiteManager
from embeddings.hybrid_retriever import HybridRetriever
from embeddings.retriever import WebsiteRetriever
from embeddings.vector_store import WebsiteVectorStore
from models.website import WebsiteStatus
from utils.exceptions import WebsiteKnowledgeError, WebsiteNotReadyError

router = APIRouter()



async def crawl(request: CrawlRequest, website_manager: WebsiteManager = Depends(get_website_manager)) -> CrawlResponse:
    try:
        record = website_manager.create(str(request.url))
        record.mark_status(WebsiteStatus.CRAWLING)
        website_manager.save(record)
        result = await AsyncWebsiteCrawler(request.max_pages, request.max_depth).crawl(str(request.url), record.website_id)
        record.statistics.pages_discovered = len(result.discovered_urls) + len(result.failed_urls)
        record.statistics.pages_crawled = len(result.documents)
        record.statistics.pages_failed = len(result.failed_urls)
        record.statistics.images_extracted = sum(len(doc.images) for doc in result.documents)
        record.statistics.tables_extracted = sum(len(doc.tables) for doc in result.documents)
        record.mark_status(WebsiteStatus.READY)
        website_manager.save(record)
        return CrawlResponse(
            website_id=record.website_id,
            url=record.normalized_url,
            pages_crawled=len(result.documents),
            failed_urls=result.failed_urls,
            documents=[doc.to_dict() for doc in result.documents],
        )
    except WebsiteKnowledgeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict()) from exc


async def index(request: IndexRequest, website_manager: WebsiteManager = Depends(get_website_manager)) -> IndexResponse:
    record = None
    try:
        record = website_manager.create(str(request.url))
        record.mark_status(WebsiteStatus.INDEXING)
        website_manager.save(record)
        result = await AsyncWebsiteCrawler(request.max_pages, request.max_depth).crawl(str(request.url), record.website_id)
        chunks = WebsiteChunker().chunk_documents(result.documents)
        documents = [chunk.to_langchain_document() for chunk in chunks]
        if request.refresh:
            try:
                WebsiteVectorStore(record.collection_name).delete_collection()
            except Exception:
                pass
        WebsiteVectorStore(record.collection_name).store_documents(documents)
        record.statistics.pages_discovered = len(result.discovered_urls) + len(result.failed_urls)
        record.statistics.pages_crawled = len(result.documents)
        record.statistics.pages_failed = len(result.failed_urls)
        record.statistics.chunks_indexed = len(chunks)
        record.statistics.images_extracted = sum(len(doc.images) for doc in result.documents)
        record.statistics.tables_extracted = sum(len(doc.tables) for doc in result.documents)
        record.statistics.code_blocks_extracted = sum(len(doc.code_blocks) for doc in result.documents)
        record.mark_status(WebsiteStatus.READY)
        website_manager.save(record)
        return IndexResponse(
            website_id=record.website_id,
            collection_name=record.collection_name,
            pages_crawled=len(result.documents),
            chunks_indexed=len(chunks),
            status=record.status.value,
        )
    except WebsiteKnowledgeError as exc:
        if record is not None:
            record.mark_status(WebsiteStatus.FAILED, error=exc.message)
            website_manager.save(record)
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict()) from exc
    except Exception as exc:
        if record is not None:
            record.mark_status(WebsiteStatus.FAILED, error=str(exc))
            website_manager.save(record)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INDEX_ERROR",
                "message": "Website indexing failed.",
                "details": {"reason": str(exc)},
            },
        ) from exc


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest, website_manager: WebsiteManager = Depends(get_website_manager)) -> RetrieveResponse:
    try:
        collection = request.collection_name
        if request.website_id:
            collection = website_manager.get(request.website_id).collection_name
        if not collection:
            ready_websites = [
                record for record in website_manager.list()
                if record.status == WebsiteStatus.READY and record.statistics.chunks_indexed > 0
            ]
            if not ready_websites:
                raise WebsiteNotReadyError(
                    "No indexed website is ready yet. Run POST /index successfully first, then retry retrieval."
                )
            ready_websites.sort(key=lambda record: record.last_indexed_at or record.updated_at, reverse=True)
            collection = ready_websites[0].collection_name
        if request.mode == "hybrid":
            results = HybridRetriever(collection).retrieve_context(request.query, k=request.k)
        else:
            results = WebsiteRetriever(collection).retrieve_context(request.query, k=request.k)
        return RetrieveResponse(query=request.query, results=results, result_count=len(results))
    except WebsiteKnowledgeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict()) from exc


@router.get("/websites", response_model=WebsiteResponse)
def websites(website_manager: WebsiteManager = Depends(get_website_manager)) -> WebsiteResponse:
    return WebsiteResponse(websites=[record.to_dict() for record in website_manager.list()])


@router.delete("/website/{website_id}")
def delete_website(website_id: str, website_manager: WebsiteManager = Depends(get_website_manager)) -> dict:
    try:
        record = website_manager.delete(website_id)
        try:
            WebsiteVectorStore(record.collection_name).delete_collection()
        except Exception:
            pass
        return {"deleted": True, "website_id": website_id}
    except WebsiteKnowledgeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict()) from exc


@router.put("/refresh", response_model=IndexResponse)
async def refresh(request: RefreshRequest, website_manager: WebsiteManager = Depends(get_website_manager)) -> IndexResponse:
    record = website_manager.get(request.website_id)
    index_request = IndexRequest(url=record.normalized_url, max_pages=request.max_pages, max_depth=request.max_depth, refresh=True)
    return await index(index_request, website_manager)


@router.get("/statistics", response_model=StatisticsResponse)
def statistics(service: StatisticsService = Depends(get_statistics_service)) -> StatisticsResponse:
    return StatisticsResponse(statistics=service.global_statistics())
