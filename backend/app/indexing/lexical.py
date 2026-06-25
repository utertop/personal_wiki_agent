from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

from app.models.chunk import Chunk


@dataclass(frozen=True)
class SearchFilters:
    """描述关键词检索的基础过滤条件，后续可继续扩展文件类型和时间范围。"""

    source_id: Optional[int] = None
    document_id: Optional[int] = None


@dataclass(frozen=True)
class SearchHit:
    """表示关键词索引返回的一条命中结果，调用方可据此定位 chunk 和来源文档。"""

    chunk_id: int
    document_id: int
    score: float
    snippet: str


class LexicalIndex(ABC):
    """关键词检索索引的抽象接口，用于隔离 SQLite FTS5、Tantivy 或 Meilisearch 等实现。"""

    @abstractmethod
    def ensure_schema(self) -> None:
        """确保关键词索引所需的底层表或外部索引已经创建。"""
        raise NotImplementedError

    @abstractmethod
    def index_chunks(self, chunks: Sequence[Chunk]) -> None:
        """把 chunk 内容写入关键词索引；重复写入同一 chunk 时应替换旧内容。"""
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, document_id: int) -> None:
        """删除指定文档在关键词索引中的全部 chunk，供文档更新或删除时调用。"""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 10,
    ) -> Sequence[SearchHit]:
        """执行关键词检索并返回按相关性排序的命中结果。"""
        raise NotImplementedError
