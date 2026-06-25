from app.indexing.embedding import HashingEmbedder
from app.indexing.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
    VectorSearchFilters,
)


def test_hashing_embedder_returns_stable_vectors_for_texts() -> None:
    """验证 HashingEmbedder 对同一文本生成稳定向量。"""

    embedder = HashingEmbedder(dimensions=8)

    first = embedder.embed_texts(["RAG knowledge base", ""])
    second = embedder.embed_texts(["RAG knowledge base"])

    assert len(first) == 2
    assert first[0].text_index == 0
    assert first[0].text == "RAG knowledge base"
    assert len(first[0].vector) == 8
    assert first[0].vector == second[0].vector
    assert first[1].vector == [0.0] * 8


def test_in_memory_vector_store_upserts_and_searches_by_similarity() -> None:
    """验证内存向量库可以写入记录并按相似度返回结果。"""

    vector_store = InMemoryVectorStore()
    vector_store.upsert(
        [
            VectorRecord(
                chunk_id=1,
                document_id=10,
                source_id=100,
                vector=[1.0, 0.0, 0.0],
                text="RAG 检索",
                metadata={"heading_path": "RAG"},
            ),
            VectorRecord(
                chunk_id=2,
                document_id=20,
                source_id=200,
                vector=[0.0, 1.0, 0.0],
                text="模型 配置",
            ),
        ]
    )

    hits = vector_store.search([0.9, 0.1, 0.0], limit=2)

    assert [hit.chunk_id for hit in hits] == [1, 2]
    assert hits[0].score > hits[1].score
    assert hits[0].document_id == 10
    assert hits[0].source_id == 100
    assert hits[0].text == "RAG 检索"
    assert hits[0].metadata["heading_path"] == "RAG"


def test_in_memory_vector_store_filters_by_source_and_document() -> None:
    """验证内存向量库支持按 source 和 document 过滤结果。"""

    vector_store = InMemoryVectorStore()
    vector_store.upsert(
        [
            VectorRecord(chunk_id=1, document_id=10, source_id=100, vector=[1.0, 0.0]),
            VectorRecord(chunk_id=2, document_id=20, source_id=200, vector=[1.0, 0.0]),
        ]
    )

    source_hits = vector_store.search(
        [1.0, 0.0],
        filters=VectorSearchFilters(source_id=200),
    )
    document_hits = vector_store.search(
        [1.0, 0.0],
        filters=VectorSearchFilters(document_id=10),
    )

    assert [hit.chunk_id for hit in source_hits] == [2]
    assert [hit.chunk_id for hit in document_hits] == [1]


def test_in_memory_vector_store_replaces_existing_chunk_vector() -> None:
    """验证重复写入同一 chunk 会替换旧向量。"""

    vector_store = InMemoryVectorStore()
    vector_store.upsert(
        [VectorRecord(chunk_id=1, document_id=10, source_id=100, vector=[1.0, 0.0])]
    )

    vector_store.upsert(
        [VectorRecord(chunk_id=1, document_id=10, source_id=100, vector=[0.0, 1.0])]
    )

    hits = vector_store.search([0.0, 1.0])
    assert [hit.chunk_id for hit in hits] == [1]
    assert hits[0].score == 1.0


def test_in_memory_vector_store_delete_document_removes_records() -> None:
    """验证删除文档会清理对应的向量记录。"""

    vector_store = InMemoryVectorStore()
    vector_store.upsert(
        [
            VectorRecord(chunk_id=1, document_id=10, source_id=100, vector=[1.0, 0.0]),
            VectorRecord(chunk_id=2, document_id=20, source_id=100, vector=[1.0, 0.0]),
        ]
    )

    vector_store.delete_document(10)

    hits = vector_store.search([1.0, 0.0], limit=10)
    assert [hit.chunk_id for hit in hits] == [2]
