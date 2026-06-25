from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class IndexJob(Base):
    """记录一次索引任务的执行状态，用于后台同步进度和失败追踪。"""

    __tablename__ = "index_jobs"

    job_id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"), nullable=False, index=True)
    status = Column(String(64), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    total_items = Column(Integer, nullable=False, default=0)
    processed_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
