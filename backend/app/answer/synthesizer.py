from dataclasses import dataclass
from typing import List, Optional

from app.answer.context_builder import AnswerCitation, AnswerContext


class AnswerSynthesisError(ValueError):
    """表示回答生成失败，例如缺少模型客户端或模型接口未实现。"""


@dataclass(frozen=True)
class RetrievalSummary:
    """描述回答使用的检索结果概况，便于前端解释答案可靠性。"""

    total_results: int
    used_results: int
    source_count: int
    has_reliable_sources: bool


@dataclass(frozen=True)
class Answer:
    """表示 Chat API 对外返回的回答结构。"""

    answer: str
    citations: List[AnswerCitation]
    confidence: float
    retrieval_summary: RetrievalSummary
    model: Optional[str] = None


class AnswerSynthesizer:
    """基于检索上下文和聊天模型客户端生成答案。"""

    def __init__(self, model_client=None, model_name: Optional[str] = None) -> None:
        """保存模型客户端；没有可靠来源时允许不配置模型。"""
        self.model_client = model_client
        self.model_name = model_name

    def generate(self, question: str, context: AnswerContext) -> Answer:
        """生成带来源引用的回答；引用只来自 AnswerContext，不从模型输出中臆造。"""
        summary = _retrieval_summary(context)
        if not context.has_reliable_sources:
            return Answer(
                answer="没有找到可靠来源，暂时不能基于个人知识库回答这个问题。",
                citations=[],
                confidence=0.0,
                retrieval_summary=summary,
                model=None,
            )
        if self.model_client is None:
            raise AnswerSynthesisError("chat_model_not_configured")

        answer_text = self._call_model(question, context)
        return Answer(
            answer=answer_text,
            citations=context.citations,
            confidence=_confidence_from_context(context),
            retrieval_summary=summary,
            model=self.model_name,
        )

    def _call_model(self, question: str, context: AnswerContext) -> str:
        """调用模型客户端；MVP 阶段约定 fake 和后续 adapter 暴露 generate_answer。"""
        generate_answer = getattr(self.model_client, "generate_answer", None)
        if generate_answer is None:
            raise AnswerSynthesisError("chat_generation_not_implemented")
        answer = generate_answer(question=question, context=context)
        answer_text = str(answer or "").strip()
        if not answer_text:
            raise AnswerSynthesisError("empty_model_answer")
        return answer_text


def _retrieval_summary(context: AnswerContext) -> RetrievalSummary:
    """从 AnswerContext 中提取检索概况。"""
    return RetrievalSummary(
        total_results=context.total_results,
        used_results=len(context.items),
        source_count=context.source_count,
        has_reliable_sources=context.has_reliable_sources,
    )


def _confidence_from_context(context: AnswerContext) -> float:
    """根据使用的上下文数量和检索分数估算回答置信度。"""
    if not context.items:
        return 0.0
    best_score = max(item.score for item in context.items)
    evidence_bonus = min(len(context.items), 3) * 0.1
    return round(min(0.95, 0.5 + evidence_bonus + min(best_score, 0.3)), 2)
