"""
HTML parsing service to extract and clean content from documentation pages.
"""
from __future__ import annotations

from bs4 import BeautifulSoup

from crawler.parser import HTMLParser
from crawler.website_processor import WebsiteProcessor
from crawler.image_extractor import extract_images
from crawler.table_extractor import extract_tables
from models.document import WebsiteDocument


class DocumentationHTMLParser:
    """
    Parses raw documentation HTML and cleans it, removing navbars, footers, scripts,
    and styles, while preserving tables, images, code blocks, and headings.
    """

    def __init__(self) -> None:
        self.parser = HTMLParser()
        self.processor = WebsiteProcessor()

    def parse(
        self,
        html: str,
        url: str,
        status_code: int = 200,
        content_type: str = "text/html",
        website_id: str | None = None,
    ) -> WebsiteDocument:
        """
        Parse raw HTML content from a URL into a WebsiteDocument.
        """
        soup = BeautifulSoup(html, "html.parser")
        images = extract_images(soup, url)
        tables = extract_tables(soup)

        parsed = self.parser.parse(html, url)
        processed = self.processor.process_text(
            parsed.text,
            code_blocks=parsed.code_blocks,
            table_texts=[table.text for table in tables],
        )

        return WebsiteDocument(
            website_id=website_id,
            source_url=url,
            title=parsed.metadata.title,
            text=processed.text,
            canonical_url=parsed.metadata.canonical_url,
            description=parsed.metadata.description,
            language=parsed.metadata.language,
            status_code=status_code,
            content_type=content_type,
            headings=parsed.metadata.headings,
            code_blocks=parsed.code_blocks,
            images=images,
            tables=tables,
            links=parsed.links,
            metadata=parsed.metadata.to_document_metadata() | {"processing": processed.to_dict()},
        )
