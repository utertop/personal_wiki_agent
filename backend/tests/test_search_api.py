from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.main import create_app
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


def make_client_with_indexed_knowledge():
    """创建带内存数据库和已索引知识内容的 API 测试客户端。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    source = SourceRepository(session).create(
        source_type="local_directory",
        name="本地资料",
        uri="E:/Knowledge",
        storage_mode="local_only",
        sync_direction="read_only",
    )
    repository = DocumentRepository(session)
    document = repository.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/rag.md",
        title="RAG 笔记",
        content_hash="hash-rag",
        mime_type="text/markdown",
        metadata_json={"relative_path": "rag.md", "tags": ["agent"]},
    )
    chunk = repository.create_chunk(
        document_id=document.document_id,
        chunk_index=0,
        text="RAG 可以把个人知识库内容检索出来，并带来源引用。",
        heading_path="RAG / 检索",
        page_number=2,
        token_count=24,
        metadata_json={"source_format": "markdown"},
    )
    SQLiteFtsIndex(session).index_chunks([chunk])
    document_id = document.document_id
    chunk_id = chunk.chunk_id
    source_id = source.source_id
    session.close()

    app = create_app()
    app.state.session_factory = session_factory
    return TestClient(app), document_id, chunk_id, source_id


def test_search_returns_traceable_results_with_document_and_source() -> None:
    """验证搜索接口返回可追溯到 chunk、document 和 source 的结果。"""

    client, document_id, chunk_id, source_id = make_client_with_indexed_knowledge()

    response = client.post("/search", json={"query": "RAG", "top_k": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "RAG"
    assert body["top_k"] == 5
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert result["chunk_id"] == chunk_id
    assert result["document"]["document_id"] == document_id
    assert result["document"]["title"] == "RAG 笔记"
    assert result["source"]["source_id"] == source_id
    assert result["source"]["name"] == "本地资料"
    assert result["citation"]["heading_path"] == "RAG / 检索"
    assert result["citation"]["page_number"] == 2
    assert "RAG" in result["snippet"]


def test_search_returns_empty_results_for_blank_query() -> None:
    """验证空白搜索不会触发底层检索，并返回空结果列表。"""

    client, _, _, _ = make_client_with_indexed_knowledge()

    response = client.post("/search", json={"query": "   "})

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_rejects_invalid_filters() -> None:
    """验证非法过滤条件会在 API 入参层被拒绝。"""

    client, _, _, _ = make_client_with_indexed_knowledge()

    response = client.post("/search", json={"query": "RAG", "source_id": -1})

    assert response.status_code == 422


def test_search_filters_results_by_file_type() -> None:
    """验证搜索接口会按文件类型过滤返回结果。"""

    client, _, _, _ = make_client_with_indexed_knowledge()

    markdown_response = client.post(
        "/search",
        json={"query": "RAG", "file_type": "markdown"},
    )
    pdf_response = client.post(
        "/search",
        json={"query": "RAG", "file_type": "pdf"},
    )

    assert markdown_response.status_code == 200
    assert len(markdown_response.json()["results"]) == 1
    assert pdf_response.status_code == 200
    assert pdf_response.json()["results"] == []


def test_document_detail_returns_chunks_and_source() -> None:
    """验证文档详情接口返回文档、数据源和 chunk 列表。"""

    client, document_id, chunk_id, source_id = make_client_with_indexed_knowledge()

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["title"] == "RAG 笔记"
    assert body["source"]["source_id"] == source_id
    assert body["metadata"]["relative_path"] == "rag.md"
    assert body["chunks"][0]["chunk_id"] == chunk_id
    assert body["chunks"][0]["heading_path"] == "RAG / 检索"


def test_chunk_detail_returns_document_and_source() -> None:
    """验证 chunk 详情接口返回片段正文、所属文档和数据源。"""

    client, document_id, chunk_id, source_id = make_client_with_indexed_knowledge()

    response = client.get(f"/chunks/{chunk_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["chunk_id"] == chunk_id
    assert body["document"]["document_id"] == document_id
    assert body["source"]["source_id"] == source_id
    assert "个人知识库" in body["text"]


def test_document_and_chunk_detail_return_404_for_missing_records() -> None:
    """验证不存在的文档和 chunk 会返回 404，方便调用方区分缺失来源。"""

    client, _, _, _ = make_client_with_indexed_knowledge()

    document_response = client.get("/documents/9999")
    chunk_response = client.get("/chunks/9999")

    assert document_response.status_code == 404
    assert chunk_response.status_code == 404
