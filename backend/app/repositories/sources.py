from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        source_type: str,
        name: str,
        uri: str,
        storage_mode: str,
        sync_direction: str,
    ) -> Source:
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
        return self.session.get(Source, source_id)

    def update(
        self,
        source_id: int,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[Source]:
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
