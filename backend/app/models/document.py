from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"), nullable=False, index=True)
    uri = Column(String(1024), nullable=False)
    title = Column(String(512), nullable=False)
    content_hash = Column(String(128), nullable=False, index=True)
    mime_type = Column(String(128), nullable=False)
    remote_id = Column(String(255), nullable=True, index=True)
    mirror_status = Column(String(64), nullable=True)
    mirror_uri = Column(String(1024), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(64), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)

    source = relationship("Source", back_populates="documents")
    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chunk.chunk_index",
    )
