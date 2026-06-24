from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.db.base import Base


class Memory(Base):
    """记录 Agent 长期记忆，必须与文档知识库 chunk 物理分离。"""

    __tablename__ = "memories"

    memory_id = Column(Integer, primary_key=True, index=True)
    memory_type = Column(String(64), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    status = Column(String(64), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
