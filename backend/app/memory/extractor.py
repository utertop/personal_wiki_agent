from dataclasses import replace
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.answer.context_builder import AnswerContext
from app.memory.store import MemoryStore
from app.models.memory import Memory


def select_memories_for_chat(session: Session, limit: int = 5) -> List[Memory]:
    """选择 Chat 生成时可用的个性化记忆，MVP 阶段按最近更新排序。"""

    return MemoryStore(session).search_memory(limit=limit)


def memories_to_context(memories: Sequence[Memory]) -> List[Dict[str, Any]]:
    """把 Memory ORM 对象转换为模型可读取、但不会成为引用来源的上下文字典。"""

    return [_memory_to_context(memory) for memory in memories]


def attach_memories_to_context(
    context: AnswerContext,
    memories: Sequence[Memory],
) -> AnswerContext:
    """把个性化记忆附加到回答上下文，同时保持 citations 只来自文档 chunk。"""

    return replace(
        context,
        personalization_memories=memories_to_context(memories),
    )


def _memory_to_context(memory: Memory) -> Dict[str, Any]:
    """把单条 Memory 转换为稳定的上下文结构。"""

    return {
        "memory_id": memory.memory_id,
        "memory_type": memory.memory_type,
        "content": memory.content,
        "source": memory.source,
        "confidence": memory.confidence,
        "created_at": _datetime_to_iso(memory.created_at),
        "updated_at": _datetime_to_iso(memory.updated_at),
        "expires_at": _datetime_to_iso(memory.expires_at),
    }


def _datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
    """把可选 datetime 转成 ISO 字符串，空值保留为 None。"""

    if value is None:
        return None
    return value.isoformat()
