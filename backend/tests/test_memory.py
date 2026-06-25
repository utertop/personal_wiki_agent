from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.llm.provider import ModelInfo
from app.main import create_app
from app.models.chunk import Chunk
from app.models.memory import Memory
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


def make_session_factory():
    """创建跨 TestClient 请求共享的内存 SQLite session factory。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def make_client(session_factory=None, model_router=None) -> TestClient:
    """创建注入测试数据库和可选模型路由器的 FastAPI 客户端。"""

    app = create_app()
    app.state.session_factory = session_factory or make_session_factory()
    if model_router is not None:
        app.state.model_router = model_router
    return TestClient(app)


def create_indexed_chunk(session_factory, text: str = "RAG 可以检索个人知识库。"):
    """创建测试数据源、文档、chunk，并把 chunk 写入 SQLite FTS。"""

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
        metadata_json={"relative_path": "rag.md", "source_format": "markdown"},
    )
    chunk = repository.create_chunk(
        document_id=document.document_id,
        chunk_index=0,
        text=text,
        heading_path="RAG",
        page_number=1,
        token_count=len(text),
        metadata_json={"source_format": "markdown"},
    )
    SQLiteFtsIndex(session).index_chunks([chunk])
    document_id = document.document_id
    chunk_id = chunk.chunk_id
    session.close()
    return document_id, chunk_id


class FakeChatModelClient:
    """记录 Chat API 传入的上下文，并返回稳定回答。"""

    def __init__(self) -> None:
        """初始化调用记录。"""

        self.last_question: Optional[str] = None
        self.last_context = None

    def generate_answer(self, question, context) -> str:
        """根据上下文中的个性化记忆数量生成可断言的回答。"""

        self.last_question = question
        self.last_context = context
        memories = getattr(context, "personalization_memories", [])
        return f"已结合 {len(memories)} 条个性化记忆回答。"


class FakeProvider:
    """为测试模型路由器提供 fake chat client。"""

    provider_id = "fake"

    def __init__(self, client: FakeChatModelClient) -> None:
        """保存 fake chat client。"""

        self.client = client

    def get_chat_client(self, model_id: str) -> FakeChatModelClient:
        """忽略模型 ID 并返回 fake chat client。"""

        return self.client


@dataclass(frozen=True)
class FakeSelection:
    """模拟模型路由器返回的模型选择结果。"""

    task: str
    provider: FakeProvider
    model: ModelInfo

    @property
    def full_name(self) -> str:
        """返回 provider/model 形式的完整模型名。"""

        return self.model.full_name


class FakeModelRouter:
    """模拟 Chat API 依赖的模型路由器。"""

    def __init__(self, client: FakeChatModelClient) -> None:
        """创建 fake provider 和模型元数据。"""

        self.last_task: Optional[str] = None
        self.provider = FakeProvider(client)
        self.model = ModelInfo(
            provider_id="fake",
            model_id="chat",
            display_name="Fake Chat",
            capabilities=["chat"],
        )

    def select_model(self, task: str) -> FakeSelection:
        """记录任务类型并返回 fake 模型选择。"""

        self.last_task = task
        return FakeSelection(task=task, provider=self.provider, model=self.model)


def test_memory_api_creates_and_lists_active_memories() -> None:
    """验证 Memory API 可以创建记忆，并按 query、type 和 limit 查询。"""

    client = make_client()

    created = client.post(
        "/memory",
        json={
            "memory_type": "user_preference",
            "content": "用户偏好中文摘要。",
            "source": "manual",
            "confidence": 0.8,
        },
    )
    client.post(
        "/memory",
        json={
            "memory_type": "project_context",
            "content": "Personal Wiki Agent 使用 RAG。",
            "source": "manual",
        },
    )
    listed = client.get("/memory", params={"query": "中文", "memory_type": "user_preference", "limit": 1})

    assert created.status_code == 200
    created_body = created.json()
    assert created_body["memory_id"] >= 1
    assert created_body["memory_type"] == "user_preference"
    assert created_body["status"] == "active"
    assert listed.status_code == 200
    assert [item["content"] for item in listed.json()["items"]] == ["用户偏好中文摘要。"]


def test_memory_api_rejects_unknown_memory_type() -> None:
    """验证 Memory API 拒绝计划外的 memory_type。"""

    client = make_client()

    response = client.post(
        "/memory",
        json={
            "memory_type": "random_note",
            "content": "不应写入的记忆。",
            "source": "manual",
        },
    )

    assert response.status_code == 422


def test_memory_store_search_excludes_expired_and_inactive_records() -> None:
    """验证 memory store 只返回 active 且未过期的记忆。"""

    from app.memory.store import MemoryStore

    session_factory = make_session_factory()
    session = session_factory()
    store = MemoryStore(session)
    active = store.remember_preference(
        content="用户偏好中文摘要。",
        source="manual",
        memory_type="user_preference",
        confidence=0.9,
    )
    session.add_all(
        [
            Memory(
                memory_type="user_preference",
                content="已经过期的中文偏好。",
                source="manual",
                confidence=1.0,
                status="active",
                expires_at=datetime.utcnow() - timedelta(days=1),
            ),
            Memory(
                memory_type="user_preference",
                content="已经归档的中文偏好。",
                source="manual",
                confidence=1.0,
                status="archived",
            ),
        ]
    )
    session.commit()

    results = store.search_memory(query="中文", memory_type="user_preference", limit=10)

    assert [memory.memory_id for memory in results] == [active.memory_id]


def test_memory_store_validates_supported_types() -> None:
    """验证 Python store 拒绝不在契约内的记忆类型。"""

    from app.memory.store import MemoryStore

    session = make_session_factory()()
    store = MemoryStore(session)

    with pytest.raises(ValueError):
        store.remember_preference(
            content="非法类型。",
            source="manual",
            memory_type="unsupported",
        )


def test_document_chunks_do_not_create_memory_or_index_memory_text() -> None:
    """验证文档 chunk 写入和 FTS 索引不会把 memory 混入知识库。"""

    session_factory = make_session_factory()
    session = session_factory()
    store_memory = Memory(
        memory_type="stable_fact",
        content="memoryonlytoken 只属于记忆。",
        source="manual",
        confidence=1.0,
    )
    session.add(store_memory)
    session.commit()
    create_indexed_chunk(session_factory, text="RAG chunkonlytoken 只属于文档。")

    lexical_hits = SQLiteFtsIndex(session).search("memoryonlytoken")
    chunk_count = session.query(Chunk).filter(Chunk.text.contains("memoryonlytoken")).count()

    assert session.query(Memory).count() == 1
    assert lexical_hits == []
    assert chunk_count == 0


def test_chat_response_separates_citations_from_memories_used() -> None:
    """验证 Chat API 把记忆作为个性化上下文返回，不把它伪装成文档引用。"""

    session_factory = make_session_factory()
    document_id, chunk_id = create_indexed_chunk(
        session_factory,
        text="RAG 可以检索个人知识库，并基于文档来源回答。",
    )
    session = session_factory()
    memory = Memory(
        memory_type="user_preference",
        content="用户希望回答优先使用中文。",
        source="manual",
        confidence=0.95,
    )
    session.add(memory)
    session.commit()
    memory_id = memory.memory_id
    session.close()
    fake_client = FakeChatModelClient()
    client = make_client(session_factory, FakeModelRouter(fake_client))

    response = client.post("/chat", json={"message": "RAG 如何帮助个人知识库？", "top_k": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["citations"][0]["document_id"] == document_id
    assert body["citations"][0]["chunk_id"] == chunk_id
    assert body["memories_used"][0]["memory_id"] == memory_id
    assert body["memories_used"][0]["content"] == "用户希望回答优先使用中文。"
    assert "memory_id" not in body["citations"][0]
    assert fake_client.last_context.personalization_memories[0]["memory_id"] == memory_id
