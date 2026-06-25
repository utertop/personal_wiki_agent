from typing import List, Optional

from sqlalchemy.orm import Session

from app.answer.context_builder import AnswerCitation, AnswerContext, AnswerContextItem
from app.answer.synthesizer import Answer, AnswerSynthesizer
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source
from app.repositories.documents import DocumentRepository


class _ExtractiveSummaryClient:
    """没有外部模型时使用的轻量抽取式总结客户端，保证工具可本地运行。"""

    def generate_answer(self, question, context) -> str:
        """基于上下文标题和片段生成简短确定性摘要。"""
        titles = []
        for item in context.items:
            title = item.citation.document_title
            if title and title not in titles:
                titles.append(title)
        joined_titles = "、".join(titles[:5]) if titles else "当前资料"
        return f"资料范围包含 {joined_titles} 等内容，可继续基于来源片段深入总结。"


def summarize_folder(
    session: Session,
    source_id: Optional[int] = None,
    path: Optional[str] = None,
    model_client=None,
    model_name: Optional[str] = None,
    max_chunks: int = 8,
) -> Answer:
    """总结指定数据源或路径下的资料，复用 Answer 模块返回带引用摘要。"""
    source = _resolve_source(session, source_id=source_id, path=path)
    if source is None:
        return AnswerSynthesizer().generate(
            "请总结这个资料范围中的主要内容。",
            AnswerContext(items=[], total_results=0),
        )

    chunks = _collect_source_chunks(session, source.source_id, max_chunks=max_chunks)
    context = _build_context_from_chunks(chunks)
    client = model_client or _ExtractiveSummaryClient()
    return AnswerSynthesizer(
        model_client=client,
        model_name=model_name or "tool/extractive-summary",
    ).generate("请总结这个资料范围中的主要内容。", context)


def _resolve_source(
    session: Session,
    source_id: Optional[int],
    path: Optional[str],
) -> Optional[Source]:
    """根据 source_id 或 path 定位数据源；两者都为空时返回 None。"""
    if source_id is not None:
        return session.get(Source, source_id)
    if path is not None:
        return session.query(Source).filter(Source.uri == path).one_or_none()
    return None


def _collect_source_chunks(session: Session, source_id: int, max_chunks: int) -> List[Chunk]:
    """按文档顺序收集数据源下的 chunk，限制数量避免一次塞入过多上下文。"""
    repository = DocumentRepository(session)
    chunks: List[Chunk] = []
    for document in repository.list_by_source_id(source_id):
        if document.status != "active":
            continue
        chunks.extend(repository.list_chunks(document.document_id))
        if len(chunks) >= max_chunks:
            return chunks[:max_chunks]
    return chunks


def _build_context_from_chunks(chunks: List[Chunk]) -> AnswerContext:
    """把 chunk 列表转换为 AnswerContext，保留文档和数据源引用信息。"""
    items: List[AnswerContextItem] = []
    for chunk in chunks:
        document: Optional[Document] = chunk.document
        source: Optional[Source] = document.source if document is not None else None
        if document is None:
            continue
        items.append(
            AnswerContextItem(
                text=chunk.text,
                score=1.0,
                citation=AnswerCitation(
                    document_id=document.document_id,
                    chunk_id=chunk.chunk_id,
                    source_id=document.source_id,
                    document_title=document.title,
                    source_name=source.name if source is not None else None,
                    heading_path=chunk.heading_path,
                    page_number=chunk.page_number,
                ),
                chunk_metadata=dict(chunk.metadata_json or {}),
                document_metadata=dict(document.metadata_json or {}),
            )
        )
    return AnswerContext(items=items, total_results=len(chunks))
