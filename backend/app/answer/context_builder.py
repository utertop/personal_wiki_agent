from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class AnswerCitation:
    """表示回答可引用的来源位置，必须能定位到 document 和 chunk。"""

    document_id: int
    chunk_id: int
    source_id: Optional[int] = None
    document_title: Optional[str] = None
    source_name: Optional[str] = None
    heading_path: Optional[str] = None
    page_number: Optional[int] = None
    snippet: Optional[str] = None


@dataclass(frozen=True)
class AnswerContextItem:
    """表示进入回答模型的一段上下文，保留正文、来源引用和元数据。"""

    text: str
    score: float
    citation: AnswerCitation
    chunk_metadata: Dict[str, Any] = field(default_factory=dict)
    document_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnswerContext:
    """表示一次回答使用的全部检索上下文，供 synthesizer 统一消费。"""

    items: List[AnswerContextItem]
    total_results: int
    personalization_memories: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def has_reliable_sources(self) -> bool:
        """判断当前上下文是否有可用于回答的可靠来源。"""
        return bool(self.items)

    @property
    def citations(self) -> List[AnswerCitation]:
        """返回全部上下文引用，回答层不得凭空添加不在此列表中的来源。"""
        return [item.citation for item in self.items]

    @property
    def source_count(self) -> int:
        """统计上下文涉及的数据源数量，供 retrieval_summary 展示。"""
        return len({item.citation.source_id for item in self.items if item.citation.source_id is not None})


def build_answer_context(
    search_results: Sequence[Any],
    max_items: int = 5,
    max_chars_per_item: int = 1200,
) -> AnswerContext:
    """把搜索结果整理为回答上下文，并保留 chunk、document 和 source 元数据。"""
    items: List[AnswerContextItem] = []
    for result in search_results[:max_items]:
        text = str(_read_field(result, "text", "") or "").strip()
        if not text:
            continue

        citation_data = _read_field(result, "citation", {})
        document_data = _read_field(result, "document", {})
        source_data = _read_field(result, "source", {})
        citation = AnswerCitation(
            document_id=int(_read_field(citation_data, "document_id", _read_field(result, "document_id", 0))),
            chunk_id=int(_read_field(citation_data, "chunk_id", _read_field(result, "chunk_id", 0))),
            source_id=_optional_int(_read_field(citation_data, "source_id", _read_field(result, "source_id", None))),
            document_title=_optional_str(_read_field(document_data, "title", None)),
            source_name=_optional_str(_read_field(source_data, "name", None)),
            heading_path=_optional_str(_read_field(citation_data, "heading_path", None)),
            page_number=_optional_int(_read_field(citation_data, "page_number", None)),
            snippet=_optional_str(_read_field(citation_data, "snippet", _read_field(result, "snippet", None))),
        )
        items.append(
            AnswerContextItem(
                text=text[:max_chars_per_item],
                score=float(_read_field(result, "score", 0.0) or 0.0),
                citation=citation,
                chunk_metadata=dict(_read_field(result, "metadata", {}) or {}),
                document_metadata=dict(_read_field(document_data, "metadata", {}) or {}),
            )
        )
    return AnswerContext(items=items, total_results=len(search_results))


def _read_field(value: Any, field_name: str, default: Any = None) -> Any:
    """同时支持从 dict、Pydantic model 或普通对象读取字段。"""
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _optional_int(value: Any) -> Optional[int]:
    """把可选数值转换为 int；空值保持 None。"""
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> Optional[str]:
    """把可选值转换为字符串；空值保持 None。"""
    if value is None:
        return None
    return str(value)
