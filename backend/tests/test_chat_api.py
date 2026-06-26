from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.llm.provider import ModelInfo
from app.main import create_app
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


class FakeChatModelClient:
    """测试用聊天模型客户端，记录收到的上下文并返回稳定答案。"""

    def __init__(self) -> None:
        """初始化调用记录，方便断言 Chat API 是否传入正确上下文。"""
        self.last_question = None
        self.last_context = None

    def generate_answer(self, question, context) -> str:
        """返回固定答案，避免测试依赖真实外部模型服务。"""
        self.last_question = question
        self.last_context = context
        return "RAG 可以先检索个人知识库，再基于来源内容回答问题。"


class FakeProvider:
    """测试用模型 provider，只负责返回 fake chat model client。"""

    provider_id = "fake"

    def __init__(self, client: FakeChatModelClient) -> None:
        """保存 fake client，供 Chat API 通过 provider 获取。"""
        self.client = client

    def get_chat_client(self, model_id: str) -> FakeChatModelClient:
        """忽略模型 id 并返回测试客户端。"""
        return self.client


@dataclass(frozen=True)
class FakeSelection:
    """测试用模型路由选择结果，模拟 ModelRouter 的返回结构。"""

    task: str
    provider: FakeProvider
    model: ModelInfo

    @property
    def full_name(self) -> str:
        """返回 fake 模型的稳定完整名称。"""
        return self.model.full_name


class FakeModelRouter:
    """测试用模型路由器，记录任务类型并返回固定模型。"""

    def __init__(self, client: FakeChatModelClient) -> None:
        """创建 fake provider 和 fake 模型元数据。"""
        self.last_task = None
        self.provider = FakeProvider(client)
        self.model = ModelInfo(
            provider_id="fake",
            model_id="chat",
            display_name="Fake Chat",
            capabilities=["chat"],
        )

    def select_model(self, task: str) -> FakeSelection:
        """记录路由任务并返回 fake 模型选择。"""
        self.last_task = task
        return FakeSelection(task=task, provider=self.provider, model=self.model)


def make_client_with_indexed_knowledge(model_router=None):
    """创建带内存数据库、FTS 索引和可选模型路由器的 Chat API 测试客户端。"""

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
        metadata_json={"relative_path": "rag.md", "source_format": "markdown"},
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
    session.close()

    app = create_app()
    app.state.session_factory = session_factory
    if model_router is not None:
        app.state.model_router = model_router
    return TestClient(app), document_id, chunk_id


def test_chat_api_generates_answer_with_traceable_citations() -> None:
    """验证 Chat API 会基于检索上下文生成答案，并返回可追溯引用。"""

    fake_client = FakeChatModelClient()
    model_router = FakeModelRouter(fake_client)
    client, document_id, chunk_id = make_client_with_indexed_knowledge(model_router)

    response = client.post(
        "/chat",
        json={"message": "RAG 怎么帮助个人知识库？", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert "RAG 可以先检索个人知识库" in body["answer"]
    assert body["confidence"] > 0
    assert body["citations"][0]["document_id"] == document_id
    assert body["citations"][0]["chunk_id"] == chunk_id
    assert body["retrieval_summary"]["used_results"] == 1
    assert body["retrieval_summary"]["source_count"] == 1
    assert body["model"] == "fake/chat"
    assert model_router.last_task == "chat"
    assert fake_client.last_question == "RAG 怎么帮助个人知识库？"
    assert fake_client.last_context.items[0].document_metadata["relative_path"] == "rag.md"


def test_chat_api_relaxes_english_question_words_for_retrieval() -> None:
    """验证英文自然问句会去掉弱问句词，避免因为 help/can 等词漏掉可靠来源。"""

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
        name="Local Notes",
        uri="E:/Knowledge",
        storage_mode="local_only",
        sync_direction="read_only",
    )
    repository = DocumentRepository(session)
    document = repository.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/rag-personal-wiki.md",
        title="RAG Personal Wiki",
        content_hash="hash-rag-english",
        mime_type="text/markdown",
        metadata_json={"relative_path": "rag-personal-wiki.md", "source_format": "markdown"},
    )
    chunk = repository.create_chunk(
        document_id=document.document_id,
        chunk_index=0,
        text="RAG helps a personal wiki answer questions with grounded citations from local notes.",
        heading_path="RAG Personal Wiki",
        page_number=None,
        token_count=13,
        metadata_json={"source_format": "markdown"},
    )
    SQLiteFtsIndex(session).index_chunks([chunk])
    document_id = document.document_id
    session.close()

    fake_client = FakeChatModelClient()
    app = create_app()
    app.state.session_factory = session_factory
    app.state.model_router = FakeModelRouter(fake_client)
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"message": "How can RAG help a personal wiki?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert "RAG 可以先检索个人知识库" in body["answer"]
    assert body["citations"][0]["document_id"] == document_id
    assert fake_client.last_question == "How can RAG help a personal wiki?"


def test_chat_api_returns_clear_message_without_reliable_sources() -> None:
    """验证没有可靠检索来源时，Chat API 不会调用模型或伪造引用。"""

    client, _, _ = make_client_with_indexed_knowledge()

    response = client.post("/chat", json={"message": "完全不存在的主题"})

    assert response.status_code == 200
    body = response.json()
    assert "没有找到可靠来源" in body["answer"]
    assert body["citations"] == []
    assert body["confidence"] == 0.0
    assert body["retrieval_summary"]["used_results"] == 0
    assert body["model"] is None


def test_chat_api_returns_understandable_error_without_model_router() -> None:
    """验证有检索来源但未配置模型路由时，Chat API 返回可理解错误。"""

    client, _, _ = make_client_with_indexed_knowledge()

    response = client.post("/chat", json={"message": "RAG 怎么帮助个人知识库？"})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "chat_model_not_configured"


def test_chat_api_rejects_invalid_top_k() -> None:
    """验证 Chat API 会拒绝非法 top_k，避免异常检索规模。"""

    fake_client = FakeChatModelClient()
    client, _, _ = make_client_with_indexed_knowledge(FakeModelRouter(fake_client))

    response = client.post("/chat", json={"message": "RAG", "top_k": 0})

    assert response.status_code == 422
