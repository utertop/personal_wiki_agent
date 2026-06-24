"""Document parser adapters."""

from app.parsers.base import PageMapEntry, ParsedSection, ParseResult, ParserAdapter
from app.parsers.docx import DocxParser
from app.parsers.html import HtmlParser
from app.parsers.markdown import MarkdownParser
from app.parsers.pdf import PdfParser
from app.parsers.text import TextParser

__all__ = [
    "DocxParser",
    "HtmlParser",
    "MarkdownParser",
    "PageMapEntry",
    "ParsedSection",
    "ParseResult",
    "ParserAdapter",
    "PdfParser",
    "TextParser",
]
