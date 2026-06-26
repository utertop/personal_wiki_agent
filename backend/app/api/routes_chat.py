import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.answer.context_builder import build_answer_context
from app.answer.synthesizer import Answer, AnswerSynthesisError, AnswerSynthesizer
from app.api.routes_search import CitationResponse, SearchResultResponse, _enrich_search_result
from app.db.session import get_db_session
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.llm.provider import ProviderConfigurationError
from app.llm.router import ModelRoutingError
from app.memory.extractor import attach_memories_to_context, memories_to_context, select_memories_for_chat
from app.retrieval.filters import SearchQuery
from app.retrieval.hybrid import HybridRetriever


router = APIRouter(tags=["chat"])


_CHAT_QUERY_STOP_WORDS = {
    "what",
    "how",
    "why",
    "is",
    "are",
    "the",
    "a",
    "an",
    "to",
    "for",
    "can",
    "could",
    "would",
    "should",
    "please",
    "help",
    "helps",
}


class ChatRequest(BaseModel):
    """描述 Chat API 入参，message 是用户问题，过滤条件用于限定知识库检索范围。"""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    source_id: Optional[int] = Field(default=None, ge=1)
    document_id: Optional[int] = Field(default=None, ge=1)
    file_type: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalSummaryResponse(BaseModel):
    """描述回答使用的检索概况。"""

    total_results: int
    used_results: int
    source_count: int
    has_reliable_sources: bool


class MemoryUsedResponse(BaseModel):
    """描述 Chat API 实际用于个性化回答的一条长期记忆。"""

    memory_id: int
    memory_type: str
    content: str
    source: str
    confidence: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None


class ChatResponse(BaseModel):
    """描述 Chat API 响应，回答必须和 citations、retrieval_summary 一起返回。"""

    answer: str
    citations: List[CitationResponse]
    confidence: float
    retrieval_summary: RetrievalSummaryResponse
    model: Optional[str] = None
    memories_used: List[MemoryUsedResponse] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    http_request: Request,
    session: Session = Depends(get_db_session),
) -> ChatResponse:
    """基于个人知识库检索结果生成带来源引用的回答。"""
    search_results = _search_for_chat(session, request)
    context = build_answer_context(search_results)
    if not context.has_reliable_sources:
        return _answer_response(AnswerSynthesizer().generate(request.message, context))

    model_router = getattr(http_request.app.state, "model_router", None)
    if model_router is None:
        raise _chat_configuration_error("chat_model_not_configured")

    memories = select_memories_for_chat(session)
    memory_context = memories_to_context(memories)
    context = attach_memories_to_context(context, memories)
    try:
        selection = model_router.select_model("chat")
        model_client = selection.provider.get_chat_client(selection.model.model_id)
        answer = AnswerSynthesizer(
            model_client=model_client,
            model_name=selection.full_name,
        ).generate(request.message, context)
    except (AnswerSynthesisError, ModelRoutingError, ProviderConfigurationError) as error:
        raise _chat_configuration_error(str(error)) from error
    return _answer_response(answer, memories_used=memory_context)


def _search_for_chat(session: Session, request: ChatRequest) -> List[SearchResultResponse]:
    """执行 Chat API 内部检索，并复用 Search API 的来源补齐逻辑。"""
    search_query = SearchQuery(
        query=_chat_search_query(request.message),
        source_id=request.source_id,
        document_id=request.document_id,
        file_type=request.file_type,
        top_k=request.top_k,
    )
    if not search_query.normalized_query:
        return []

    retriever = HybridRetriever(lexical_index=SQLiteFtsIndex(session))
    return [
        enriched
        for result in retriever.search(search_query)
        for enriched in [_enrich_search_result(session, result, file_type=request.file_type)]
        if enriched is not None
    ]


def _chat_search_query(message: str) -> str:
    """从自然语言问题中提取轻量检索词，MVP 阶段优先保留英文术语。"""
    tokens = re.findall(r"[A-Za-z0-9_+#.-]+", message)
    keyword_tokens = [
        token.strip(".,?!:;")
        for token in tokens
        if token.strip(".,?!:;").lower() not in _CHAT_QUERY_STOP_WORDS
    ]
    return " ".join(keyword_tokens) if keyword_tokens else message


def _answer_response(
    answer: Answer,
    memories_used: Optional[Sequence[Dict[str, Any]]] = None,
) -> ChatResponse:
    """把 Answer dataclass 转换为 FastAPI 响应模型。"""
    return ChatResponse(
        answer=answer.answer,
        citations=[
            CitationResponse(
                document_id=citation.document_id,
                chunk_id=citation.chunk_id,
                source_id=citation.source_id,
                heading_path=citation.heading_path,
                page_number=citation.page_number,
                snippet=citation.snippet,
            )
            for citation in answer.citations
        ],
        confidence=answer.confidence,
        retrieval_summary=RetrievalSummaryResponse(**asdict(answer.retrieval_summary)),
        model=answer.model,
        memories_used=[
            MemoryUsedResponse(**memory)
            for memory in (memories_used or [])
        ],
    )


def _chat_configuration_error(code: str) -> HTTPException:
    """构造可理解的 Chat API 配置错误响应。"""
    return HTTPException(
        status_code=503,
        detail={
            "code": code,
            "message": _error_message(code),
        },
    )


def _error_message(code: str) -> str:
    """把内部错误码转换为用户可理解的中文说明。"""
    messages: Dict[str, str] = {
        "chat_model_not_configured": "还没有配置可用的聊天模型，请先配置 ModelRouter 或 chat provider。",
        "chat_generation_not_implemented": "当前模型客户端还没有实现真实回答生成能力。",
        "empty_model_answer": "聊天模型返回了空答案，请检查模型服务或提示词配置。",
    }
    return messages.get(code, f"聊天模型配置不可用：{code}")
