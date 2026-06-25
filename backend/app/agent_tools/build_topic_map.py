from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.answer.context_builder import AnswerCitation
from app.agent_tools.search_notes import search_notes
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source
from app.repositories.documents import DocumentRepository


@dataclass(frozen=True)
class TopicEntry:
    """表示主题地图中的一个主题节点，第一版只保留文档和引用关系。"""

    label: str
    document_ids: List[int] = field(default_factory=list)
    citations: List[AnswerCitation] = field(default_factory=list)


@dataclass(frozen=True)
class TopicMap:
    """表示 Agent 工具生成的轻量主题地图。"""

    query: Optional[str]
    source_id: Optional[int]
    topics: List[TopicEntry]


def build_topic_map(
    session: Session,
    query: Optional[str] = None,
    source_id: Optional[int] = None,
    top_k: int = 10,
) -> TopicMap:
    """生成第一版主题地图，按 heading 或文档标题聚合来源引用。"""
    if query:
        return _topic_map_from_search(session, query=query, source_id=source_id, top_k=top_k)
    return _topic_map_from_source(session, source_id=source_id, top_k=top_k)


def _topic_map_from_search(
    session: Session,
    query: str,
    source_id: Optional[int],
    top_k: int,
) -> TopicMap:
    """基于检索结果生成主题地图，适合围绕某个问题整理资料。"""
    search_response = search_notes(session, query=query, source_id=source_id, top_k=top_k)
    grouped: Dict[str, TopicEntry] = {}
    for result in search_response.results:
        label = _topic_label(result.citation.heading_path, result.document.title)
        entry = grouped.setdefault(label, TopicEntry(label=label))
        _append_unique_document(entry.document_ids, result.document_id)
        entry.citations.append(
            AnswerCitation(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                source_id=result.source_id,
                document_title=result.document.title,
                source_name=result.source.name,
                heading_path=result.citation.heading_path,
                page_number=result.citation.page_number,
                snippet=result.snippet,
            )
        )
    return TopicMap(query=query, source_id=source_id, topics=list(grouped.values()))


def _topic_map_from_source(
    session: Session,
    source_id: Optional[int],
    top_k: int,
) -> TopicMap:
    """基于数据源下的 chunk 生成主题地图，适合做资料范围总览。"""
    if source_id is None:
        return TopicMap(query=None, source_id=None, topics=[])

    source = session.get(Source, source_id)
    if source is None:
        return TopicMap(query=None, source_id=source_id, topics=[])

    repository = DocumentRepository(session)
    grouped: Dict[str, TopicEntry] = {}
    used = 0
    for document in repository.list_by_source_id(source_id):
        if document.status != "active":
            continue
        for chunk in repository.list_chunks(document.document_id):
            if used >= top_k:
                return TopicMap(query=None, source_id=source_id, topics=list(grouped.values()))
            _add_chunk_topic(grouped, document, chunk, source)
            used += 1
    return TopicMap(query=None, source_id=source_id, topics=list(grouped.values()))


def _add_chunk_topic(
    grouped: Dict[str, TopicEntry],
    document: Document,
    chunk: Chunk,
    source: Source,
) -> None:
    """把一个 chunk 加入主题聚合结果。"""
    label = _topic_label(chunk.heading_path, document.title)
    entry = grouped.setdefault(label, TopicEntry(label=label))
    _append_unique_document(entry.document_ids, document.document_id)
    entry.citations.append(
        AnswerCitation(
            document_id=document.document_id,
            chunk_id=chunk.chunk_id,
            source_id=source.source_id,
            document_title=document.title,
            source_name=source.name,
            heading_path=chunk.heading_path,
            page_number=chunk.page_number,
        )
    )


def _topic_label(heading_path: Optional[str], document_title: str) -> str:
    """从 heading_path 中提取一级主题；没有标题时回退到文档标题。"""
    if heading_path:
        return heading_path.split("/", 1)[0].strip()
    return document_title


def _append_unique_document(document_ids: List[int], document_id: int) -> None:
    """保持文档 id 顺序去重，方便主题地图稳定输出。"""
    if document_id not in document_ids:
        document_ids.append(document_id)
