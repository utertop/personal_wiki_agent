from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.db.base import Base
from app.indexing.lexical import SearchFilters
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


def make_session():
    """创建测试用内存数据库会话，并加载索引相关模型表。"""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def create_chunk(session, text, source_name="测试资料", title="note"):
    """创建带所属数据源和文档的测试 chunk。"""

    source = SourceRepository(session).create(
        source_type="local_directory",
        name=source_name,
        uri=f"/tmp/{source_name}",
        storage_mode="local_only",
        sync_direction="read_only",
    )
    repository = DocumentRepository(session)
    document = repository.create_document(
        source_id=source.source_id,
        uri=f"/tmp/{source_name}/{title}.md",
        title=title,
        content_hash=f"hash-{source_name}-{title}",
        mime_type="text/markdown",
    )
    chunk = repository.create_chunk(
        document_id=document.document_id,
        chunk_index=0,
        text=text,
        heading_path="知识库",
        page_number=None,
        token_count=len(text),
    )
    return source, document, chunk


def test_sqlite_fts_indexes_chunks_and_returns_snippet() -> None:
    """验证 SQLite FTS 可以索引 chunk 并返回高亮摘要。"""

    session = make_session()
    _, document, chunk = create_chunk(
        session,
        "RAG pipeline stores document chunks for retrieval.",
    )
    lexical_index = SQLiteFtsIndex(session)

    lexical_index.index_chunks([chunk])
    hits = lexical_index.search("RAG")

    assert len(hits) == 1
    assert hits[0].chunk_id == chunk.chunk_id
    assert hits[0].document_id == document.document_id
    assert hits[0].score > 0
    assert "<mark>RAG</mark>" in hits[0].snippet


def test_sqlite_fts_supports_basic_chinese_keyword_and_source_filter() -> None:
    """验证 SQLite FTS 支持基础中文关键词和数据源过滤。"""

    session = make_session()
    first_source, _, first_chunk = create_chunk(
        session,
        "中文 检索 知识库 可以 命中 关键词",
        source_name="第一资料",
    )
    second_source, _, second_chunk = create_chunk(
        session,
        "另一个 知识库 文档 用于 过滤 测试",
        source_name="第二资料",
    )
    lexical_index = SQLiteFtsIndex(session)
    lexical_index.index_chunks([first_chunk, second_chunk])

    hits = lexical_index.search("知识库", filters=SearchFilters(source_id=first_source.source_id))
    missed = lexical_index.search("知识库", filters=SearchFilters(source_id=9999))

    assert [hit.chunk_id for hit in hits] == [first_chunk.chunk_id]
    assert missed == []
    assert second_source.source_id != first_source.source_id


def test_sqlite_fts_replaces_existing_chunk_text() -> None:
    """验证重复索引同一 chunk 时会替换旧文本。"""

    session = make_session()
    _, _, chunk = create_chunk(session, "旧内容 legacy keyword")
    lexical_index = SQLiteFtsIndex(session)

    lexical_index.index_chunks([chunk])
    chunk.text = "新内容 current keyword"
    session.commit()
    lexical_index.index_chunks([chunk])

    assert lexical_index.search("legacy") == []
    assert lexical_index.search("current")[0].chunk_id == chunk.chunk_id


def test_sqlite_fts_delete_document_removes_hits() -> None:
    """验证删除文档索引后不再返回相关关键词命中。"""

    session = make_session()
    _, document, chunk = create_chunk(session, "delete target keyword")
    lexical_index = SQLiteFtsIndex(session)

    lexical_index.index_chunks([chunk])
    lexical_index.delete_document(document.document_id)

    assert lexical_index.search("target") == []
