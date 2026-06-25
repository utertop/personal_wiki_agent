from pathlib import Path
from typing import Dict, List, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.indexing.lexical import LexicalIndex, SearchFilters, SearchHit
from app.models.chunk import Chunk
from app.models.document import Document


class SQLiteFtsIndex(LexicalIndex):
    """基于 SQLite FTS5 的关键词索引实现，适合 MVP 阶段的本地个人知识库。"""

    def __init__(self, session: Session, table_name: str = "chunk_fts") -> None:
        """保存数据库 session 和 FTS 表名，并延迟到首次使用时创建索引表。"""
        self.session = session
        self.table_name = table_name
        self._schema_ready = False

    def ensure_schema(self) -> None:
        """创建 FTS5 虚拟表；chunk_id、document_id 和 source_id 只用于过滤不参与分词。"""
        if self._schema_ready:
            return

        self.session.execute(
            text(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name}
                USING fts5(
                    chunk_id UNINDEXED,
                    document_id UNINDEXED,
                    source_id UNINDEXED,
                    text,
                    heading_path,
                    tokenize = 'unicode61'
                )
                """
            )
        )
        self.session.commit()
        self._schema_ready = True

    def index_chunks(self, chunks: Sequence[Chunk]) -> None:
        """把一组 chunk 写入 FTS5；写入前先删除同 chunk_id 的旧记录，保证重复索引可替换。"""
        self.ensure_schema()
        for chunk in chunks:
            document = self._document_for_chunk(chunk)
            if document is None:
                continue
            self._delete_chunk(chunk.chunk_id)
            self.session.execute(
                text(
                    f"""
                    INSERT INTO {self.table_name}
                    (chunk_id, document_id, source_id, text, heading_path)
                    VALUES (:chunk_id, :document_id, :source_id, :text, :heading_path)
                    """
                ),
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "source_id": document.source_id,
                    "text": chunk.text,
                    "heading_path": chunk.heading_path or "",
                },
            )
        self.session.commit()

    def delete_document(self, document_id: int) -> None:
        """删除指定文档在 FTS5 中的所有索引记录，用于文档删除或更新前清理。"""
        self.ensure_schema()
        self.session.execute(
            text(f"DELETE FROM {self.table_name} WHERE document_id = :document_id"),
            {"document_id": document_id},
        )
        self.session.commit()

    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 10,
    ) -> List[SearchHit]:
        """用 FTS5 MATCH 执行关键词检索，并返回 snippet 和相关性分数。"""
        self.ensure_schema()
        match_query = _match_query(query)
        if not match_query or limit <= 0:
            return []

        where_clauses = [f"{self.table_name} MATCH :query"]
        params: Dict[str, object] = {
            "query": match_query,
            "limit": limit,
        }
        if filters is not None and filters.source_id is not None:
            where_clauses.append("source_id = :source_id")
            params["source_id"] = filters.source_id
        if filters is not None and filters.document_id is not None:
            where_clauses.append("document_id = :document_id")
            params["document_id"] = filters.document_id

        rows = self.session.execute(
            text(
                f"""
                SELECT
                    chunk_id,
                    document_id,
                    bm25({self.table_name}) AS rank,
                    snippet({self.table_name}, 3, '<mark>', '</mark>', '...', 24) AS snippet
                FROM {self.table_name}
                WHERE {" AND ".join(where_clauses)}
                ORDER BY rank
                LIMIT :limit
                """
            ),
            params,
        ).mappings()

        return [
            SearchHit(
                chunk_id=int(row["chunk_id"]),
                document_id=int(row["document_id"]),
                score=_score_from_rank(float(row["rank"])),
                snippet=str(row["snippet"] or ""),
            )
            for row in rows
        ]

    def _delete_chunk(self, chunk_id: int) -> None:
        """删除单个 chunk 的旧 FTS 记录，供重复索引时做幂等替换。"""
        self.session.execute(
            text(f"DELETE FROM {self.table_name} WHERE chunk_id = :chunk_id"),
            {"chunk_id": chunk_id},
        )

    def _document_for_chunk(self, chunk: Chunk) -> Optional[Document]:
        """根据 chunk 关联或数据库查询获取文档，用于补齐 source_id 过滤字段。"""
        if chunk.document is not None:
            return chunk.document
        return self.session.get(Document, chunk.document_id)


def _match_query(query: str) -> str:
    """把用户输入转换为较安全的 FTS5 查询，MVP 阶段按空白分词并逐词精确匹配。"""
    terms = [
        term.strip().replace('"', '""')
        for term in query.split()
        if term.strip()
    ]
    return " ".join(f'"{term}"' for term in terms)


def _score_from_rank(rank: float) -> float:
    """把 FTS5 越小越好的 rank 转成越大越好的正向分数，方便上层统一排序。"""
    if rank < 0:
        return abs(rank)
    return 1.0 / (1.0 + rank)
