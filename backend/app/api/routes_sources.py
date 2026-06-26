from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.sources import SourceRepository


router = APIRouter(tags=["sources"])

SUPPORTED_SOURCE_TYPES = {
    "local_directory",
    "local_synced_notes",
    "obsidian_vault",
}


class SourceCreateRequest(BaseModel):
    """描述创建数据源的 API 入参，MVP 阶段只开放本地优先 source 类型。"""

    model_config = ConfigDict(extra="forbid")

    source_type: str
    name: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    storage_mode: str = "local_only"
    sync_direction: str = "read_only"
    enabled: bool = True

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        """校验 source_type 是否已有可执行 connector。"""

        normalized = value.strip()
        if normalized not in SUPPORTED_SOURCE_TYPES:
            allowed = ", ".join(sorted(SUPPORTED_SOURCE_TYPES))
            raise ValueError(f"source_type 必须是以下之一：{allowed}")
        return normalized


class SourceResponse(BaseModel):
    """描述 API 返回的一条数据源记录。"""

    model_config = ConfigDict(from_attributes=True)

    source_id: int
    source_type: str
    name: str
    uri: str
    storage_mode: str
    sync_direction: str
    enabled: bool
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SourceListResponse(BaseModel):
    """描述数据源列表响应。"""

    items: List[SourceResponse]


@router.get("/sources", response_model=SourceListResponse)
def list_sources(session: Session = Depends(get_db_session)) -> SourceListResponse:
    """列出当前数据库中的全部数据源。"""

    sources = SourceRepository(session).list_all()
    return SourceListResponse(items=[SourceResponse.model_validate(source) for source in sources])


@router.post("/sources", response_model=SourceResponse)
def create_source(
    request: SourceCreateRequest,
    session: Session = Depends(get_db_session),
) -> SourceResponse:
    """创建一个本地优先数据源，供后续索引任务使用。"""

    try:
        source = SourceRepository(session).create(
            source_type=request.source_type,
            name=request.name.strip(),
            uri=request.uri.strip(),
            storage_mode=request.storage_mode.strip(),
            sync_direction=request.sync_direction.strip(),
            enabled=request.enabled,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return SourceResponse.model_validate(source)
