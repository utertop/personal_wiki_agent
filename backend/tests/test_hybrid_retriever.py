from app.indexing.embedding import EmbeddingResult
from app.indexing.lexical import LexicalIndex, SearchFilters, SearchHit
from app.indexing.vector_store import VectorSearchFilters, VectorSearchHit, VectorStore
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.filters import SearchQuery


class FakeLexicalIndex(LexicalIndex):
    """用于测试 HybridRetriever 的关键词索引替身。"""

    def __init__(self, hits):
        """记录预设命中结果，并保留最近一次检索入参。"""

        self.hits = hits
        self.last_query = None
        self.last_filters = None
        self.last_limit = None

    def ensure_schema(self) -> None:
        """测试替身无需创建真实索引结构。"""

        pass

    def index_chunks(self, chunks) -> None:
        """测试替身不执行真实 chunk 写入。"""

        pass

    def delete_document(self, document_id: int) -> None:
        """测试替身不执行真实文档删除。"""

        pass

    def search(self, query: str, filters=None, limit: int = 10):
        """返回预设关键词命中，并记录检索参数。"""

        self.last_query = query
        self.last_filters = filters
        self.last_limit = limit
        return self.hits[:limit]


class FakeVectorStore(VectorStore):
    """用于测试 HybridRetriever 的向量库替身。"""

    def __init__(self, hits):
        """记录预设向量命中结果，并保留最近一次查询向量。"""

        self.hits = hits
        self.last_query_vector = None
        self.last_filters = None
        self.last_limit = None

    def upsert(self, records) -> None:
        """测试替身不执行真实向量写入。"""

        pass

    def search(self, query_vector, filters=None, limit: int = 10):
        """返回预设向量命中，并记录查询向量和过滤条件。"""

        self.last_query_vector = list(query_vector)
        self.last_filters = filters
        self.last_limit = limit
        return self.hits[:limit]

    def delete_document(self, document_id: int) -> None:
        """测试替身不执行真实向量删除。"""

        pass


class FakeEmbedder:
    """用于测试检索流程的固定向量生成器。"""

    def embed_texts(self, texts):
        """为输入文本返回确定性的单条测试向量。"""

        return [
            EmbeddingResult(
                text_index=0,
                text=texts[0],
                vector=[1.0, 0.0, 0.0],
            )
        ]


def test_hybrid_retriever_returns_lexical_results_without_vector_store() -> None:
    """验证没有向量库时 HybridRetriever 仍可返回关键词检索结果。"""

    lexical_index = FakeLexicalIndex(
        [
            SearchHit(
                chunk_id=1,
                document_id=10,
                score=0.8,
                snippet="<mark>RAG</mark> 内容",
            )
        ]
    )
    retriever = HybridRetriever(lexical_index=lexical_index)

    results = retriever.search(SearchQuery(query="RAG", source_id=100, top_k=5))

    assert len(results) == 1
    assert results[0].chunk_id == 1
    assert results[0].document_id == 10
    assert results[0].lexical_score == 0.8
    assert results[0].vector_score == 0.0
    assert results[0].snippet == "<mark>RAG</mark> 内容"
    assert results[0].citation.chunk_id == 1
    assert isinstance(lexical_index.last_filters, SearchFilters)
    assert lexical_index.last_filters.source_id == 100
    assert lexical_index.last_limit == 10


def test_hybrid_retriever_merges_duplicate_lexical_and_vector_hits() -> None:
    """验证混合检索会合并同一 chunk 的关键词和向量命中。"""

    lexical_index = FakeLexicalIndex(
        [
            SearchHit(chunk_id=1, document_id=10, score=0.7, snippet="lexical"),
            SearchHit(chunk_id=2, document_id=20, score=0.6, snippet="only lexical"),
        ]
    )
    vector_store = FakeVectorStore(
        [
            VectorSearchHit(
                chunk_id=1,
                document_id=10,
                source_id=100,
                score=0.9,
                text="merged text",
                metadata={"heading_path": "RAG", "page_number": 3},
            ),
            VectorSearchHit(
                chunk_id=3,
                document_id=30,
                source_id=100,
                score=0.8,
                text="only vector",
            ),
        ]
    )
    retriever = HybridRetriever(
        lexical_index=lexical_index,
        vector_store=vector_store,
        embedder=FakeEmbedder(),
    )

    results = retriever.search(SearchQuery(query="RAG", top_k=3))

    assert [result.chunk_id for result in results] == [1, 3, 2]
    assert results[0].lexical_score == 0.7
    assert results[0].vector_score == 0.9
    assert results[0].text == "merged text"
    assert results[0].citation.heading_path == "RAG"
    assert results[0].citation.page_number == 3


def test_hybrid_retriever_passes_filters_to_lexical_and_vector_indexes() -> None:
    """验证检索过滤条件会同时传递给关键词索引和向量库。"""

    lexical_index = FakeLexicalIndex([])
    vector_store = FakeVectorStore([])
    retriever = HybridRetriever(
        lexical_index=lexical_index,
        vector_store=vector_store,
        embedder=FakeEmbedder(),
    )

    results = retriever.search(
        SearchQuery(
            query="知识库",
            source_id=7,
            document_id=9,
            file_type="markdown",
            top_k=4,
        )
    )

    assert results == []
    assert lexical_index.last_query == "知识库"
    assert lexical_index.last_filters == SearchFilters(source_id=7, document_id=9)
    assert vector_store.last_query_vector == [1.0, 0.0, 0.0]
    assert vector_store.last_filters == VectorSearchFilters(source_id=7, document_id=9)
    assert vector_store.last_limit == 8


def test_hybrid_retriever_returns_empty_for_blank_query() -> None:
    """验证空白查询会直接返回空结果并跳过底层检索。"""

    lexical_index = FakeLexicalIndex(
        [SearchHit(chunk_id=1, document_id=10, score=0.8, snippet="ignored")]
    )
    retriever = HybridRetriever(lexical_index=lexical_index)

    assert retriever.search(SearchQuery(query="   ")) == []
    assert lexical_index.last_query is None
