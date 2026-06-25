from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from app.indexing.embedding import Embedder
from app.indexing.lexical import LexicalIndex, SearchFilters, SearchHit
from app.indexing.vector_store import VectorSearchFilters, VectorSearchHit, VectorStore
from app.retrieval.filters import SearchQuery
from app.retrieval.ranking import combine_scores, sort_by_score


@dataclass(frozen=True)
class SourceCitation:
    """表示检索结果的来源定位信息，供回答层生成可追溯引用。"""

    document_id: int
    chunk_id: int
    source_id: Optional[int] = None
    heading_path: Optional[str] = None
    page_number: Optional[int] = None
    snippet: Optional[str] = None


@dataclass(frozen=True)
class SearchResult:
    """表示 HybridRetriever 合并后的统一检索结果。"""

    chunk_id: int
    document_id: int
    score: float
    citation: SourceCitation
    source_id: Optional[int] = None
    lexical_score: float = 0.0
    vector_score: float = 0.0
    text: Optional[str] = None
    snippet: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _Candidate:
    """内部候选结果，用于在 lexical 和 vector 命中之间按 chunk_id 合并。"""

    chunk_id: int
    document_id: int
    source_id: Optional[int] = None
    lexical_score: float = 0.0
    vector_score: float = 0.0
    text: Optional[str] = None
    snippet: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """合并关键词召回、向量召回和过滤条件的检索编排器。"""

    def __init__(
        self,
        lexical_index: LexicalIndex,
        vector_store: Optional[VectorStore] = None,
        embedder: Optional[Embedder] = None,
        lexical_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> None:
        """保存底层检索依赖；未配置向量库时仍可只依赖关键词检索工作。"""
        self.lexical_index = lexical_index
        self.vector_store = vector_store
        self.embedder = embedder
        self.lexical_weight = lexical_weight
        self.vector_weight = vector_weight

    def search(self, search_query: SearchQuery) -> List[SearchResult]:
        """执行 hybrid search：先召回，再按 chunk_id 合并，最后统一排序和截断。"""
        query = search_query.normalized_query
        if not query:
            return []

        candidates: Dict[int, _Candidate] = {}
        self._merge_lexical_hits(
            candidates,
            self._search_lexical(query, search_query),
            fallback_source_id=search_query.source_id,
        )
        self._merge_vector_hits(
            candidates,
            self._search_vector(query, search_query),
        )
        results = [
            self._build_result(candidate)
            for candidate in candidates.values()
        ]
        return sort_by_score(results)[: search_query.top_k]

    def _search_lexical(self, query: str, search_query: SearchQuery) -> Sequence[SearchHit]:
        """调用关键词索引，并把统一过滤条件转换为 SearchFilters。"""
        return self.lexical_index.search(
            query,
            filters=SearchFilters(
                source_id=search_query.source_id,
                document_id=search_query.document_id,
            ),
            limit=search_query.candidate_limit,
        )

    def _search_vector(self, query: str, search_query: SearchQuery) -> Sequence[VectorSearchHit]:
        """在配置了 embedder 和 vector store 时执行向量召回，否则返回空列表。"""
        if self.vector_store is None or self.embedder is None:
            return []
        embedding = self.embedder.embed_texts([query])[0]
        return self.vector_store.search(
            embedding.vector,
            filters=VectorSearchFilters(
                source_id=search_query.source_id,
                document_id=search_query.document_id,
            ),
            limit=search_query.candidate_limit,
        )

    def _merge_lexical_hits(
        self,
        candidates: Dict[int, _Candidate],
        hits: Sequence[SearchHit],
        fallback_source_id: Optional[int],
    ) -> None:
        """把关键词命中合并到内部候选表，保留 snippet 和 lexical score。"""
        for hit in hits:
            candidate = candidates.setdefault(
                hit.chunk_id,
                _Candidate(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    source_id=fallback_source_id,
                    metadata={},
                ),
            )
            candidate.lexical_score = max(candidate.lexical_score, hit.score)
            candidate.snippet = hit.snippet

    def _merge_vector_hits(
        self,
        candidates: Dict[int, _Candidate],
        hits: Sequence[VectorSearchHit],
    ) -> None:
        """把向量命中合并到内部候选表，补充 source、text、metadata 和 vector score。"""
        for hit in hits:
            candidate = candidates.setdefault(
                hit.chunk_id,
                _Candidate(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    source_id=hit.source_id,
                    metadata={},
                ),
            )
            candidate.document_id = hit.document_id
            candidate.source_id = hit.source_id
            candidate.vector_score = max(candidate.vector_score, hit.score)
            candidate.text = hit.text
            candidate.metadata = dict(hit.metadata)

    def _build_result(self, candidate: _Candidate) -> SearchResult:
        """把内部候选对象转换为对外返回的 SearchResult。"""
        metadata = dict(candidate.metadata or {})
        snippet = candidate.snippet
        citation = SourceCitation(
            document_id=candidate.document_id,
            chunk_id=candidate.chunk_id,
            source_id=candidate.source_id,
            heading_path=metadata.get("heading_path"),
            page_number=metadata.get("page_number"),
            snippet=snippet,
        )
        score = combine_scores(
            candidate.lexical_score,
            candidate.vector_score,
            lexical_weight=self.lexical_weight,
            vector_weight=self.vector_weight,
        )
        return SearchResult(
            chunk_id=candidate.chunk_id,
            document_id=candidate.document_id,
            source_id=candidate.source_id,
            score=score,
            lexical_score=candidate.lexical_score,
            vector_score=candidate.vector_score,
            text=candidate.text,
            snippet=snippet,
            metadata=metadata,
            citation=citation,
        )
