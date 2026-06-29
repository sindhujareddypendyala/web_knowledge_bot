# Web Knowledge Bot Backend

Backend, PDF RAG, and AI integration module for the Web Knowledge Bot project.

This module is responsible for:

- FastAPI backend APIs
- Multiple PDF upload
- PDF text extraction and chunking
- Gemini embedding generation
- ChromaDB vector storage
- Semantic PDF retrieval
- Gemini 2.5 Flash answer generation
- Source attribution
- SQLite chat history
- Future website retriever integration

It does not include frontend code or website crawler code.

## Setup

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL_NAME=gemini-2.5-flash
EMBEDDING_MODEL_NAME=models/gemini-embedding-001
```

Run the API:

```bash
uvicorn app:app --reload
```

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Backend health check |
| `POST` | `/upload_pdf` | Upload and index one or more PDFs |
| `POST` | `/chat` | Ask a question using indexed knowledge |
| `GET` | `/documents` | List indexed PDF documents |
| `DELETE` | `/documents/{document_id}` | Delete an indexed document |
| `GET` | `/history` | Fetch chat history |

## RAG Flow

1. User uploads PDF files.
2. Backend validates and saves each PDF.
3. Text is extracted page by page using PyPDF.
4. Text is split with recursive character chunking.
5. Chunks are embedded with Google Generative AI embeddings.
6. Chunks and metadata are stored in ChromaDB.
7. User asks a question through `/chat`.
8. Relevant chunks are retrieved by semantic search.
9. Context and question are sent to Gemini 2.5 Flash.
10. Response is returned with source references.

## Chat Request Example

```json
{
  "question": "What does the uploaded manual say about authentication?",
  "session_id": "optional-session-id",
  "source_types": ["pdf"],
  "top_k": 5
}
```

## Anti-Hallucination Behavior

The LLM prompt requires Gemini to answer only from retrieved context. If the indexed knowledge does not contain the answer, the API returns:

```text
I could not find this answer in the indexed knowledge. Please upload or index a source that contains the relevant information.
```

## Future Website Integration

Member 2 can expose a function shaped like:

```python
def retrieve_website(query: str, top_k: int):
    ...
```

The backend can adapt it through `integrations.website_interface.build_website_retriever()` and inject it into the RAG pipeline without changing the API response shape.

## Storage

- Uploaded PDFs: `uploads/`
- ChromaDB vectors: `vector_db/`
- Temporary files: `temp/`
- SQLite chat history: `database/chat_history.sqlite3`
