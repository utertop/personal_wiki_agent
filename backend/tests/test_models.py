from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.chunk import Chunk
from app.models.memory import Memory
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


def make_session():
    """创建测试用内存数据库会话，并初始化 ORM 表结构。"""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_source_document_and_chunk_round_trip() -> None:
    """验证数据源、文档和 chunk 可以完成基础写入与读取闭环。"""

    session = make_session()
    source_repo = SourceRepository(session)
    document_repo = DocumentRepository(session)

    source = source_repo.create(
        source_type="local_directory",
        name="本地资料",
        uri="E:/Knowledge",
        storage_mode="local_only",
        sync_direction="read_only",
    )
    document = document_repo.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/rag.md",
        title="RAG 笔记",
        content_hash="hash-1",
        mime_type="text/markdown",
    )
    document_repo.create_chunk(
        document_id=document.document_id,
        chunk_index=0,
        text="RAG 是检索增强生成。",
        heading_path="RAG",
        page_number=None,
        token_count=12,
    )

    loaded = document_repo.get_document(document.document_id)

    assert loaded is not None
    assert loaded.title == "RAG 笔记"
    assert len(loaded.chunks) == 1
    assert loaded.chunks[0].text == "RAG 是检索增强生成。"


def test_repositories_update_source_and_document_status() -> None:
    """验证 repository 可以更新数据源信息和文档状态。"""

    session = make_session()
    source_repo = SourceRepository(session)
    document_repo = DocumentRepository(session)

    source = source_repo.create(
        source_type="local_directory",
        name="旧资料库",
        uri="E:/Knowledge",
        storage_mode="local_only",
        sync_direction="read_only",
    )
    document = document_repo.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/old.md",
        title="旧文档",
        content_hash="hash-1",
        mime_type="text/markdown",
    )

    updated_source = source_repo.update(source.source_id, name="新资料库", enabled=False)
    updated_document = document_repo.update_document_status(document.document_id, "deleted")

    assert updated_source is not None
    assert updated_source.name == "新资料库"
    assert updated_source.enabled is False
    assert updated_document is not None
    assert updated_document.status == "deleted"


def test_memory_is_stored_separately_from_document_chunks() -> None:
    """验证长期记忆与文档 chunk 使用独立数据表存储。"""

    session = make_session()
    memory = Memory(
        memory_type="user_preference",
        content="用户偏好中文文档。",
        source="manual",
        confidence=0.9,
    )
    chunk = Chunk(
        document_id=1,
        chunk_index=0,
        text="文档事实。",
        token_count=4,
    )

    session.add(memory)
    session.add(chunk)
    session.commit()

    assert session.query(Memory).count() == 1
    assert session.query(Chunk).count() == 1
    assert Memory.__tablename__ != Chunk.__tablename__
