import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class VectorRecord:
    """表示准备写入向量库的一条 chunk 向量记录。"""

    chunk_id: int
    document_id: int
    source_id: int
    vector: List[float]
    text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorSearchFilters:
    """描述向量检索的基础过滤条件，保持和关键词检索过滤模型对齐。"""

    source_id: Optional[int] = None
    document_id: Optional[int] = None


@dataclass(frozen=True)
class VectorSearchHit:
    """表示向量检索返回的一条命中结果，供后续 hybrid retriever 合并排序。"""

    chunk_id: int
    document_id: int
    source_id: int
    score: float
    text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """向量库抽象接口，用于隔离内存实现、sqlite-vec、Chroma、LanceDB 或 Qdrant。"""

    @abstractmethod
    def upsert(self, records: Sequence[VectorRecord]) -> None:
        """写入或替换一批 chunk 向量记录；同一 chunk_id 重复写入应覆盖旧值。"""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_vector: Sequence[float],
        filters: Optional[VectorSearchFilters] = None,
        limit: int = 10,
    ) -> List[VectorSearchHit]:
        """按向量相似度检索 chunk，并按分数从高到低返回。"""
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, document_id: int) -> None:
        """删除指定文档的全部向量记录，用于文档重建或删除时保持索引一致。"""
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """内存型 VectorStore，适合测试和 MVP 早期无外部向量库时验证接口闭环。"""

    def __init__(self) -> None:
        """初始化 chunk_id 到向量记录的内存映射；进程退出后数据不会持久化。"""
        self._records: Dict[int, VectorRecord] = {}

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        """按 chunk_id 写入或替换向量记录，保持调用方可重复索引同一文档。"""
        for record in records:
            self._records[record.chunk_id] = record

    def search(
        self,
        query_vector: Sequence[float],
        filters: Optional[VectorSearchFilters] = None,
        limit: int = 10,
    ) -> List[VectorSearchHit]:
        """使用余弦相似度进行内存检索，并应用 source/document 过滤。"""
        if limit <= 0:
            return []

        hits = [
            VectorSearchHit(
                chunk_id=record.chunk_id,
                document_id=record.document_id,
                source_id=record.source_id,
                score=_cosine_similarity(query_vector, record.vector),
                text=record.text,
                metadata=dict(record.metadata),
            )
            for record in self._records.values()
            if _matches_filters(record, filters)
        ]
        hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return hits[:limit]

    def delete_document(self, document_id: int) -> None:
        """从内存索引中删除指定文档的所有 chunk 向量。"""
        self._records = {
            chunk_id: record
            for chunk_id, record in self._records.items()
            if record.document_id != document_id
        }


def _matches_filters(record: VectorRecord, filters: Optional[VectorSearchFilters]) -> bool:
    """判断向量记录是否命中过滤条件；未传过滤条件时全部保留。"""
    if filters is None:
        return True
    if filters.source_id is not None and record.source_id != filters.source_id:
        return False
    if filters.document_id is not None and record.document_id != filters.document_id:
        return False
    return True


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """计算两个向量的余弦相似度；维度不一致时按共同长度比较。"""
    size = min(len(left), len(right))
    if size == 0:
        return 0.0

    left_values = list(left[:size])
    right_values = list(right[:size])
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    dot_product = sum(left_values[index] * right_values[index] for index in range(size))
    return dot_product / (left_norm * right_norm)
