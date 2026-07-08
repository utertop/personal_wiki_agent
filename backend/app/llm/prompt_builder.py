from typing import Any, Dict, List

from app.answer.context_builder import AnswerContext, AnswerContextItem


SYSTEM_PROMPT = (
    "你是 Personal Wiki Agent。只能基于用户给定的个人知识库资料回答；"
    "如果资料不足，请明确说明不足，不要编造来源。"
)


def build_chat_messages(question: str, context: AnswerContext) -> List[Dict[str, str]]:
    """Build shared chat messages for model providers."""

    context_blocks = "\n\n".join(
        format_context_item(index, item)
        for index, item in enumerate(context.items, start=1)
    )
    memory_blocks = "\n".join(
        f"- {memory.get('memory_type', 'memory')}: {memory.get('content', '')}"
        for memory in context.personalization_memories
        if str(memory.get("content", "")).strip()
    )
    user_parts = [
        f"问题：{question.strip()}",
        "可用资料：",
        context_blocks or "无",
    ]
    if memory_blocks:
        user_parts.extend(["个性化记忆：", memory_blocks])

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "\n\n".join(user_parts),
        },
    ]


def format_context_item(index: int, item: AnswerContextItem) -> str:
    """Format one retrieved chunk with stable source metadata."""

    citation = item.citation
    label_parts = [
        f"document_id={citation.document_id}",
        f"chunk_id={citation.chunk_id}",
    ]
    if citation.document_title:
        label_parts.append(f"title={citation.document_title}")
    if citation.heading_path:
        label_parts.append(f"heading={citation.heading_path}")
    return f"[{index}] {'; '.join(label_parts)}\n{item.text.strip()}"
