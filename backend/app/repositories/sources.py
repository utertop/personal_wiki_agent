from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:
    """封装 Source 表的基础读写操作，避免业务层直接操作 ORM 细节。"""

    def __init__(self, session: Session) -> None:
        """保存当前请求或任务使用的数据库 session。"""
        self.session = session

    def create(
        self,
        source_type: str,
        name: str,
        uri: str,
        storage_mode: str,
        sync_direction: str,
    ) -> Source:
        """创建一个数据源记录，并返回带主键的 ORM 对象。"""
        source = Source(
            source_type=source_type,
            name=name,
            uri=uri,
            storage_mode=storage_mode,
            sync_direction=sync_direction,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get(self, source_id: int) -> Optional[Source]:
        """按主键查询数据源；不存在时返回 None。"""
        return self.session.get(Source, source_id)

    def update(
        self,
        source_id: int,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[Source]:
        """更新数据源的基础可变字段，并刷新更新时间。"""
        source = self.get(source_id)
        if source is None:
            return None

        if name is not None:
            source.name = name
        if enabled is not None:
            source.enabled = enabled
        source.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(source)
        return source
