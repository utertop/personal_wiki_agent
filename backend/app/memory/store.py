from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import _get_default_session_factory
from app.models.memory import Memory


ALLOWED_MEMORY_TYPES = {
    "user_preference",
    "project_context",
    "workflow_habit",
    "stable_fact",
}


class MemoryStore:
    """封装长期记忆的最小读写能力，并确保它不依赖文档 chunk 表。"""

    def __init__(self, session: Session) -> None:
        """保存当前请求或任务使用的数据库 session。"""

        self.session = session

    def remember_preference(
        self,
        content: str,
        source: str,
        memory_type: str = "user_preference",
        confidence: float = 1.0,
        expires_at: Optional[datetime] = None,
    ) -> Memory:
        """写入一条 active 记忆，默认用于保存用户偏好。"""

        normalized_type = validate_memory_type(memory_type)
        normalized_content = _clean_required_text(content, "content")
        normalized_source = _clean_required_text(source, "source")
        normalized_confidence = _validate_confidence(confidence)
        memory = Memory(
            memory_type=normalized_type,
            content=normalized_content,
            source=normalized_source,
            confidence=normalized_confidence,
            status="active",
            expires_at=_normalize_datetime(expires_at),
        )
        self.session.add(memory)
        self.session.commit()
        self.session.refresh(memory)
        return memory

    def search_memory(
        self,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Memory]:
        """查询 active 且未过期的记忆，可按内容关键词和类型缩小范围。"""

        normalized_limit = _validate_limit(limit)
        now = datetime.utcnow()
        statement = self.session.query(Memory).filter(
            Memory.status == "active",
            or_(Memory.expires_at.is_(None), Memory.expires_at > now),
        )
        if memory_type is not None:
            statement = statement.filter(Memory.memory_type == validate_memory_type(memory_type))

        normalized_query = (query or "").strip()
        if normalized_query:
            pattern = f"%{normalized_query}%"
            statement = statement.filter(
                or_(
                    Memory.content.ilike(pattern),
                    Memory.source.ilike(pattern),
                )
            )

        return (
            statement.order_by(Memory.updated_at.desc(), Memory.memory_id.desc())
            .limit(normalized_limit)
            .all()
        )


def remember_preference(
    content: str,
    source: str,
    memory_type: str = "user_preference",
    confidence: float = 1.0,
    expires_at: Optional[datetime] = None,
) -> Memory:
    """使用默认数据库 session 写入一条长期记忆，供非 API 调用方复用。"""

    session_factory = _get_default_session_factory()
    session = session_factory()
    try:
        return MemoryStore(session).remember_preference(
            content=content,
            source=source,
            memory_type=memory_type,
            confidence=confidence,
            expires_at=expires_at,
        )
    finally:
        session.close()


def search_memory(
    query: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 20,
) -> List[Memory]:
    """使用默认数据库 session 查询 active 且未过期的长期记忆。"""

    session_factory = _get_default_session_factory()
    session = session_factory()
    try:
        return MemoryStore(session).search_memory(
            query=query,
            memory_type=memory_type,
            limit=limit,
        )
    finally:
        session.close()


def validate_memory_type(memory_type: str) -> str:
    """校验并返回契约允许的 memory_type。"""

    normalized = (memory_type or "").strip()
    if normalized not in ALLOWED_MEMORY_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MEMORY_TYPES))
        raise ValueError(f"memory_type 必须是以下之一：{allowed}")
    return normalized


def _clean_required_text(value: str, field_name: str) -> str:
    """清理必填文本字段，并拒绝空字符串。"""

    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} 不能为空")
    return cleaned


def _validate_confidence(confidence: float) -> float:
    """校验置信度范围，返回 float 形式的值。"""

    value = float(confidence)
    if value < 0.0 or value > 1.0:
        raise ValueError("confidence 必须在 0 到 1 之间")
    return value


def _validate_limit(limit: int) -> int:
    """校验查询数量上限，避免一次读取过多记忆。"""

    value = int(limit)
    if value < 1:
        raise ValueError("limit 必须大于 0")
    return min(value, 100)


def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """把带时区时间转换为 UTC 朴素时间，保持数据库比较一致。"""

    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
