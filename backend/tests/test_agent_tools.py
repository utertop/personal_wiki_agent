from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent_tools.build_topic_map import build_topic_map
from app.agent_tools.open_source import open_source
from app.agent_tools.search_notes import search_notes
from app.agent_tools.summarize_folder import summarize_folder
from app.db.base import Base
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


class FakeSummaryClient:
    """测试用总结模型客户端，记录 Answer 模块收到的上下文。"""

    def __init__(self) -> None:
        """初始化调用记录，便于断言工具层是否正确构造上下文。"""
        self.last_question = None
        self.last_context = None

    def generate_answer(self, question, context) -> str:
        """返回固定摘要文本，避免测试依赖真实模型服务。"""
        self.last_question = question
        self.last_context = context
        return "资料夹摘要：包含 RAG 检索、来源引用和模型配置笔记。"


def make_session_with_agent_knowledge():
    """创建带两篇文档和 FTS 索引的测试数据库会话。"""

    engine = create_engine("sqlite:///:memory:")
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
    rag_document = repository.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/rag.md",
        title="RAG 笔记",
        content_hash="hash-rag",
        mime_type="text/markdown",
        metadata_json={"relative_path": "rag.md", "source_format": "markdown"},
    )
    rag_chunk = repository.create_chunk(
        document_id=rag_document.document_id,
        chunk_index=0,
        text="RAG 可以检索个人知识库，并把回答绑定到来源引用。",
        heading_path="RAG / 检索",
        page_number=1,
        token_count=22,
        metadata_json={"source_format": "markdown"},
    )
    model_document = repository.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/model.md",
        title="模型配置",
        content_hash="hash-model",
        mime_type="text/markdown",
        metadata_json={"relative_path": "model.md", "source_format": "markdown"},
    )
    model_chunk = repository.create_chunk(
        document_id=model_document.document_id,
        chunk_index=0,
        text="模型配置需要通过 ModelProvider 和 ModelRouter 管理。",
        heading_path="模型 / 配置",
        page_number=None,
        token_count=18,
        metadata_json={"source_format": "markdown"},
    )
    SQLiteFtsIndex(session).index_chunks([rag_chunk, model_chunk])
    return session, source.source_id, rag_document.document_id, rag_chunk.chunk_id


def test_search_notes_tool_returns_traceable_results() -> None:
    """验证 search_notes 工具会调用检索层并返回可追溯结果。"""

    session, source_id, document_id, chunk_id = make_session_with_agent_knowledge()

    result = search_notes(session, query="RAG", source_id=source_id, top_k=3)

    assert result.query == "RAG"
    assert len(result.results) == 1
    assert result.results[0].chunk_id == chunk_id
    assert result.results[0].document.document_id == document_id
    assert result.results[0].source.source_id == source_id
    assert result.results[0].citation.heading_path == "RAG / 检索"


def test_open_source_tool_opens_document_or_chunk() -> None:
    """验证 open_source 工具可以按 document_id 或 chunk_id 打开来源。"""

    session, source_id, document_id, chunk_id = make_session_with_agent_knowledge()

    document_detail = open_source(session, document_id=document_id)
    chunk_detail = open_source(session, chunk_id=chunk_id)

    assert document_detail.document_id == document_id
    assert document_detail.source.source_id == source_id
    assert document_detail.chunks[0].chunk_id == chunk_id
    assert chunk_detail.chunk_id == chunk_id
    assert chunk_detail.document.document_id == document_id
    assert chunk_detail.source.source_id == source_id


def test_summarize_folder_tool_uses_answer_context() -> None:
    """验证 summarize_folder 工具基于 source 下的 chunk 构造 AnswerContext。"""

    session, source_id, document_id, _ = make_session_with_agent_knowledge()
    fake_client = FakeSummaryClient()

    summary = summarize_folder(
        session,
        source_id=source_id,
        model_client=fake_client,
        model_name="fake/summary",
    )

    assert "资料夹摘要" in summary.answer
    assert summary.model == "fake/summary"
    assert summary.retrieval_summary.used_results == 2
    assert summary.citations[0].document_id == document_id
    assert fake_client.last_question == "请总结这个资料范围中的主要内容。"
    assert fake_client.last_context.items[0].document_metadata["relative_path"] == "rag.md"


def test_build_topic_map_tool_groups_results_by_heading() -> None:
    """验证 build_topic_map 工具会生成第一版主题列表和来源引用。"""

    session, source_id, document_id, chunk_id = make_session_with_agent_knowledge()

    topic_map = build_topic_map(session, query="RAG", source_id=source_id, top_k=5)

    assert topic_map.query == "RAG"
    assert topic_map.source_id == source_id
    assert [topic.label for topic in topic_map.topics] == ["RAG"]
    assert topic_map.topics[0].document_ids == [document_id]
    assert topic_map.topics[0].citations[0].chunk_id == chunk_id
