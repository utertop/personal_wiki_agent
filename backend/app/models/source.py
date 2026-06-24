from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Source(Base):
    """记录一个知识数据源，例如本地目录、同步笔记目录或云端笔记。"""

    __tablename__ = "sources"

    source_id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    uri = Column(String(1024), nullable=False)
    storage_mode = Column(String(64), nullable=False, default="local_only")
    sync_direction = Column(String(64), nullable=False, default="read_only")
    config_hash = Column(String(128), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    documents = relationship("Document", back_populates="source")
