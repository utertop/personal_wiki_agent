import json
import math
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
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


class SQLiteVectorStore(VectorStore):
    """SQLite-backed VectorStore for local persistent semantic retrieval."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO vector_records (
                    chunk_id,
                    document_id,
                    source_id,
                    vector_json,
                    text,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    document_id = excluded.document_id,
                    source_id = excluded.source_id,
                    vector_json = excluded.vector_json,
                    text = excluded.text,
                    metadata_json = excluded.metadata_json
                """,
                [
                    (
                        record.chunk_id,
                        record.document_id,
                        record.source_id,
                        json.dumps(list(record.vector)),
                        record.text,
                        json.dumps(record.metadata, ensure_ascii=False),
                    )
                    for record in records
                ],
            )

    def search(
        self,
        query_vector: Sequence[float],
        filters: Optional[VectorSearchFilters] = None,
        limit: int = 10,
    ) -> List[VectorSearchHit]:
        if limit <= 0:
            return []

        where_clauses: List[str] = []
        params: List[int] = []
        if filters is not None and filters.source_id is not None:
            where_clauses.append("source_id = ?")
            params.append(filters.source_id)
        if filters is not None and filters.document_id is not None:
            where_clauses.append("document_id = ?")
            params.append(filters.document_id)
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT chunk_id, document_id, source_id, vector_json, text, metadata_json
                FROM vector_records
                {where_sql}
                """,
                params,
            ).fetchall()

        hits = [
            VectorSearchHit(
                chunk_id=int(row["chunk_id"]),
                document_id=int(row["document_id"]),
                source_id=int(row["source_id"]),
                score=_cosine_similarity(query_vector, _loads_vector(row["vector_json"])),
                text=row["text"],
                metadata=_loads_metadata(row["metadata_json"]),
            )
            for row in rows
        ]
        hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return hits[:limit]

    def delete_document(self, document_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM vector_records WHERE document_id = ?",
                (document_id,),
            )

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_records (
                    chunk_id INTEGER PRIMARY KEY,
                    document_id INTEGER NOT NULL,
                    source_id INTEGER NOT NULL,
                    vector_json TEXT NOT NULL,
                    text TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_vector_records_document_id ON vector_records(document_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_vector_records_source_id ON vector_records(source_id)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        return connection


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


def _loads_vector(raw_value: str) -> List[float]:
    values = json.loads(raw_value)
    if not isinstance(values, list):
        return []
    return [float(value) for value in values]


def _loads_metadata(raw_value: str) -> Dict[str, Any]:
    values = json.loads(raw_value or "{}")
    return values if isinstance(values, dict) else {}
