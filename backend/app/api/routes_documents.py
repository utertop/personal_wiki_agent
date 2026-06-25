from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes_search import DocumentSummary, SourceSummary
from app.db.session import get_db_session
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source
from app.repositories.documents import DocumentRepository


router = APIRouter(tags=["documents"])


class ChunkSummary(BaseModel):
    """描述文档详情中的 chunk 摘要，保留打开来源所需的定位信息。"""

    chunk_id: int
    document_id: int
    chunk_index: int
    heading_path: Optional[str] = None
    page_number: Optional[int] = None
    token_count: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentDetailResponse(BaseModel):
    """描述文档详情接口响应，包含来源信息和文档下的 chunk 列表。"""

    document_id: int
    source_id: int
    title: str
    uri: str
    mime_type: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: SourceSummary
    chunks: List[ChunkSummary]


class ChunkDetailResponse(BaseModel):
    """描述 chunk 详情接口响应，包含片段正文和所属文档、数据源。"""

    chunk_id: int
    document_id: int
    chunk_index: int
    text: str
    heading_path: Optional[str] = None
    page_number: Optional[int] = None
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document: DocumentSummary
    source: SourceSummary


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document_detail(
    document_id: int = Path(ge=1),
    session: Session = Depends(get_db_session),
) -> DocumentDetailResponse:
    """返回单个文档详情，供前端或 Agent 打开搜索结果来源。"""
    repository = DocumentRepository(session)
    document = repository.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document_not_found")
    source = session.get(Source, document.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")

    return DocumentDetailResponse(
        document_id=document.document_id,
        source_id=document.source_id,
        title=document.title,
        uri=document.uri,
        mime_type=document.mime_type,
        status=document.status,
        metadata=dict(document.metadata_json or {}),
        source=_source_summary(source),
        chunks=[_chunk_summary(chunk) for chunk in repository.list_chunks(document.document_id)],
    )


@router.get("/chunks/{chunk_id}", response_model=ChunkDetailResponse)
def get_chunk_detail(
    chunk_id: int = Path(ge=1),
    session: Session = Depends(get_db_session),
) -> ChunkDetailResponse:
    """返回单个 chunk 详情，供来源引用和原文定位使用。"""
    repository = DocumentRepository(session)
    chunk = repository.get_chunk(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="chunk_not_found")
    document = session.get(Document, chunk.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document_not_found")
    source = session.get(Source, document.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")

    return ChunkDetailResponse(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        heading_path=chunk.heading_path,
        page_number=chunk.page_number,
        token_count=chunk.token_count,
        metadata=dict(chunk.metadata_json or {}),
        document=_document_summary(document),
        source=_source_summary(source),
    )


def _chunk_summary(chunk: Chunk) -> ChunkSummary:
    """把 Chunk ORM 对象转换为文档详情中的稳定摘要。"""
    return ChunkSummary(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        heading_path=chunk.heading_path,
        page_number=chunk.page_number,
        token_count=chunk.token_count,
        text=chunk.text,
        metadata=dict(chunk.metadata_json or {}),
    )


def _document_summary(document: Document) -> DocumentSummary:
    """把 Document ORM 对象转换为 chunk 详情中的文档摘要。"""
    return DocumentSummary(
        document_id=document.document_id,
        title=document.title,
        uri=document.uri,
        mime_type=document.mime_type,
        status=document.status,
        metadata=dict(document.metadata_json or {}),
    )


def _source_summary(source: Source) -> SourceSummary:
    """把 Source ORM 对象转换为详情接口中的数据源摘要。"""
    return SourceSummary(
        source_id=source.source_id,
        source_type=source.source_type,
        name=source.name,
        uri=source.uri,
    )
