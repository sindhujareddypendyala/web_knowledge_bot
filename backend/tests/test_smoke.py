from crawler.website_chunker import WebsiteChunker
from models.document import WebsiteDocument
from utils.validators import normalize_url


def test_url_normalization_strips_tracking_and_fragment():
    assert normalize_url("Example.com/docs?utm_source=x&b=2#top") == "https://example.com/docs?b=2"


def test_chunker_creates_chunks_without_langchain_runtime():
    document = WebsiteDocument(
        website_id="site",
        source_url="https://example.com",
        title="Docs",
        text="hello world " * 200,
    )
    chunks = WebsiteChunker(chunk_size=100, chunk_overlap=20).chunk_documents([document])
    assert chunks
    assert chunks[0].source_url == "https://example.com"
