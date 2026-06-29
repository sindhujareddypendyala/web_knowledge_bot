# Website Knowledge RAG

Backend-only Website Knowledge Module for the Web Knowledge Bot.

This module crawls documentation websites, respects `robots.txt`, reads
sitemaps, extracts and cleans HTML content, chunks documents, stores embeddings
in ChromaDB, and returns ranked RAG context for another backend module.

No frontend is included.

## Features

- Robots.txt policy checks
- Sitemap discovery and sitemap-index parsing
- Sync crawler plus async FastAPI facade
- Retry handling for transient fetch failures
- URL normalization and duplicate detection
- Metadata, code block, image, table, and link extraction
- Clean chunk-ready text processing
- Recursive chunking with LangChain fallback-safe wrappers
- Google Gemini or HuggingFace embeddings
- ChromaDB vector storage
- Vector and hybrid retrieval with confidence scores
- Multi-website registry and per-website Chroma collections
- Website refresh, delete, statistics, cache, and backend context export

## API Endpoints

- `POST /crawl`
- `POST /index`
- `POST /retrieve`
- `GET /websites`
- `DELETE /website/{website_id}`
- `PUT /refresh`
- `GET /statistics`
- `GET /health`

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
GOOGLE_API_KEY=your_google_key_optional
EMBEDDING_PROVIDER=auto
MAX_PAGES_PER_SITE=25
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

If `GOOGLE_API_KEY` is not set, the module falls back to HuggingFace
embeddings.

## Run API

```bash
uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Example Flow

Index a documentation website:

```bash
curl -X POST http://127.0.0.1:8000/index ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://docs.python.org/3/\",\"max_pages\":10,\"max_depth\":2}"
```

Retrieve context:

```bash
curl -X POST http://127.0.0.1:8000/retrieve ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"How do I create a virtual environment?\",\"k\":5,\"mode\":\"hybrid\"}"
```

## CLI Compatibility

The original CLI runner still exists:

```bash
python main.py
```

## Important Files

- `app.py` - FastAPI application entrypoint
- `api/routes.py` - API endpoints
- `crawler/crawler.py` - crawl orchestration
- `crawler/async_crawler.py` - async crawler facade
- `crawler/parser.py` - HTML parsing
- `crawler/website_processor.py` - text cleaning
- `crawler/website_chunker.py` - chunk creation
- `embeddings/vector_store.py` - Chroma vector store wrapper
- `embeddings/retriever.py` - vector retrieval
- `embeddings/hybrid_retriever.py` - hybrid retrieval
- `database/website_manager.py` - website registry
- `integrations/backend_interface.py` - context export boundary

## Verification

```bash
python -m compileall .
python -m pytest tests
```
