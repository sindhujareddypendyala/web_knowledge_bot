"""
Website Knowledge RAG — end-to-end pipeline runner.

    1. Crawl the website                 (crawler.crawler)
    2. Chunk the cleaned page text       (crawler.website_chunker)
    3. Embed + store chunks in ChromaDB  (embeddings.vector_store)
    4. Let the user ask questions        (embeddings.retriever)

Run with:  python main.py
"""
import config
from crawler.crawler import crawl_website
from crawler.website_chunker import chunk_documents
from embeddings.vector_store import store_embeddings
from embeddings.retriever import retrieve
from database.chat_history import create_session, add_message
from utils.logger import get_logger

logger = get_logger(__name__)


def index_website(url: str) -> int:
    """Runs steps 1-3: crawl -> chunk -> embed & store. Returns #chunks stored."""
    print("🚀 Starting crawl...\n")
    pages = crawl_website(url, max_pages=config.MAX_PAGES_PER_SITE, delay=config.CRAWL_DELAY_SECONDS)

    if not pages:
        print("❌ No pages were crawled. Check the URL and try again.")
        return 0

    print(f"\n✅ Crawled {len(pages)} page(s)")
    if pages:
        print("\n🔍 Sample cleaned content:")
        print("--- Page 1 ---")
        print(pages[0]["text"][:300])

    print("\n✂️  Chunking text...")
    chunks = chunk_documents(pages, chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    print(f"   Created {len(chunks)} chunk(s)")

    print("\n🧠 Generating embeddings & storing in ChromaDB...")
    store_embeddings(chunks, collection_name=config.DEFAULT_COLLECTION_NAME)
    print(f"✅ Indexed {len(chunks)} chunk(s) into '{config.DEFAULT_COLLECTION_NAME}'")

    return len(chunks)


def chat_loop():
    """Simple terminal Q&A loop against the indexed website."""
    session_id = create_session()
    print("\n💬 Ask questions about the site (type 'exit' to quit)\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            continue

        add_message(session_id, "user", query)
        results = retrieve(query, k=5, collection_name=config.DEFAULT_COLLECTION_NAME)

        if not results:
            print("Bot: I couldn't find anything relevant on this site for that.\n")
            continue

        print("\nBot: Here's what I found:")
        for i, r in enumerate(results, start=1):
            print(f"  {i}. ({r['title']}) {r['text'][:200]}...")
            print(f"     source: {r['source_url']}")
        print()

        add_message(session_id, "assistant", str(results))


def main():
    print("=" * 50)
    print("Website Knowledge RAG")
    print("=" * 50)

    url = input("Enter Website URL: ").strip()
    print(f"\nWebsite URL Received: {url}\n")

    n_chunks = index_website(url)
    if n_chunks > 0:
        chat_loop()


if __name__ == "__main__":
    main()
