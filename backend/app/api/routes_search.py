from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source
from app.retrieval.filters import SearchQuery
from app.retrieval.hybrid import HybridRetriever, SearchResult


router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    """描述搜索 API 入参，限制过滤条件和返回数量的基础边界。"""

    model_config = ConfigDict(extra="forbid")

    query: str
    source_id: Optional[int] = Field(default=None, ge=1)
    document_id: Optional[int] = Field(default=None, ge=1)
    file_type: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=50)


class SourceSummary(BaseModel):
    """描述 API 返回中的数据源摘要，避免调用方读取完整 ORM 对象。"""

    source_id: int
    source_type: str
    name: str
    uri: str


class DocumentSummary(BaseModel):
    """描述 API 返回中的文档摘要，供搜索结果和 chunk 详情复用。"""

    document_id: int
    title: str
    uri: str
    mime_type: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CitationResponse(BaseModel):
    """描述可追溯引用信息，用于回答层和前端打开来源。"""

    document_id: int
    chunk_id: int
    source_id: Optional[int] = None
    heading_path: Optional[str] = None
    page_number: Optional[int] = None
    snippet: Optional[str] = None


class SearchResultResponse(BaseModel):
    """描述搜索接口返回的单条命中，聚合检索分数、来源和正文片段。"""

    chunk_id: int
    document_id: int
    source_id: int
    score: float
    lexical_score: float
    vector_score: float
    text: str
    snippet: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    citation: CitationResponse
    document: DocumentSummary
    source: SourceSummary


class SearchResponse(BaseModel):
    """描述搜索接口响应，保留原始查询、top_k 和命中结果列表。"""

    query: str
    top_k: int
    results: List[SearchResultResponse]


@router.post("/search", response_model=SearchResponse)
def search_notes(
    request: SearchRequest,
    session: Session = Depends(get_db_session),
) -> SearchResponse:
    """执行知识库搜索，并返回可追溯到来源文档和 chunk 的结果。"""
    search_query = SearchQuery(
        query=request.query,
        source_id=request.source_id,
        document_id=request.document_id,
        file_type=request.file_type,
        top_k=request.top_k,
    )
    if not search_query.normalized_query:
        return SearchResponse(query=request.query, top_k=request.top_k, results=[])

    retriever = HybridRetriever(lexical_index=SQLiteFtsIndex(session))
    results = [
        enriched
        for result in retriever.search(search_query)
        for enriched in [_enrich_search_result(session, result, file_type=request.file_type)]
        if enriched is not None
    ]
    return SearchResponse(query=request.query, top_k=request.top_k, results=results)


def _enrich_search_result(
    session: Session,
    result: SearchResult,
    file_type: Optional[str] = None,
) -> Optional[SearchResultResponse]:
    """用数据库中的 chunk、document 和 source 补齐检索结果的来源详情。"""
    chunk = session.get(Chunk, result.chunk_id)
    if chunk is None:
        return None
    document = session.get(Document, result.document_id)
    if document is None or document.status != "active":
        return None
    if file_type is not None and not _matches_file_type(document, file_type):
        return None
    source = session.get(Source, document.source_id)
    if source is None:
        return None

    metadata = dict(chunk.metadata_json or {})
    heading_path = result.citation.heading_path or chunk.heading_path
    page_number = result.citation.page_number or chunk.page_number
    snippet = result.snippet or result.citation.snippet
    citation = CitationResponse(
        document_id=document.document_id,
        chunk_id=chunk.chunk_id,
        source_id=source.source_id,
        heading_path=heading_path,
        page_number=page_number,
        snippet=snippet,
    )
    return SearchResultResponse(
        chunk_id=chunk.chunk_id,
        document_id=document.document_id,
        source_id=source.source_id,
        score=result.score,
        lexical_score=result.lexical_score,
        vector_score=result.vector_score,
        text=result.text or chunk.text,
        snippet=snippet,
        metadata=metadata,
        citation=citation,
        document=_document_summary(document),
        source=_source_summary(source),
    )


def _document_summary(document: Document) -> DocumentSummary:
    """把 Document ORM 对象转换为稳定的 API 摘要模型。"""
    return DocumentSummary(
        document_id=document.document_id,
        title=document.title,
        uri=document.uri,
        mime_type=document.mime_type,
        status=document.status,
        metadata=dict(document.metadata_json or {}),
    )


def _matches_file_type(document: Document, file_type: str) -> bool:
    """判断文档是否匹配请求的文件类型过滤条件。"""
    normalized = file_type.strip().lower().lstrip(".")
    aliases = {
        "md": "markdown",
        "markdown": "markdown",
        "txt": "text",
        "text": "text",
        "pdf": "pdf",
        "docx": "docx",
        "word": "docx",
        "html": "html",
        "htm": "html",
    }
    expected = aliases.get(normalized, normalized)
    metadata = document.metadata_json or {}
    source_format = str(metadata.get("source_format") or "").lower()
    mime_type = (document.mime_type or "").lower()
    uri = (document.uri or "").lower()

    if source_format == expected:
        return True
    if expected == "markdown":
        return mime_type in {"text/markdown", "text/x-markdown"} or uri.endswith((".md", ".markdown"))
    if expected == "text":
        return mime_type == "text/plain" or uri.endswith(".txt")
    if expected == "pdf":
        return mime_type == "application/pdf" or uri.endswith(".pdf")
    if expected == "docx":
        return (
            mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or uri.endswith(".docx")
        )
    if expected == "html":
        return mime_type in {"text/html", "application/xhtml+xml"} or uri.endswith((".html", ".htm"))
    return source_format == expected or uri.endswith(f".{expected}")


def _source_summary(source: Source) -> SourceSummary:
    """把 Source ORM 对象转换为稳定的 API 摘要模型。"""
    return SourceSummary(
        source_id=source.source_id,
        source_type=source.source_type,
        name=source.name,
        uri=source.uri,
    )
