from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.memory.store import MemoryStore, validate_memory_status, validate_memory_type


router = APIRouter(tags=["memory"])


class MemoryCreateRequest(BaseModel):
    """描述创建长期记忆的 API 入参。"""

    model_config = ConfigDict(extra="forbid")

    memory_type: str
    content: str = Field(min_length=1)
    source: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    expires_at: Optional[datetime] = None

    @field_validator("memory_type")
    @classmethod
    def validate_supported_memory_type(cls, value: str) -> str:
        """校验 memory_type 是否属于共享契约允许的集合。"""

        return validate_memory_type(value)


class MemoryUpdateRequest(BaseModel):
    """Describe editable long-term memory fields."""

    model_config = ConfigDict(extra="forbid")

    memory_type: Optional[str] = None
    content: Optional[str] = Field(default=None, min_length=1)
    source: Optional[str] = Field(default=None, min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    expires_at: Optional[datetime] = None
    status: Optional[str] = None

    @field_validator("memory_type")
    @classmethod
    def validate_supported_memory_type(cls, value: Optional[str]) -> Optional[str]:
        """Validate memory_type when the request updates it."""

        if value is None:
            return value
        return validate_memory_type(value)

    @field_validator("status")
    @classmethod
    def validate_supported_status(cls, value: Optional[str]) -> Optional[str]:
        """Validate memory lifecycle status when the request updates it."""

        if value is None:
            return value
        return validate_memory_status(value)


class MemoryResponse(BaseModel):
    """描述 API 返回的一条长期记忆。"""

    model_config = ConfigDict(from_attributes=True)

    memory_id: int
    memory_type: str
    content: str
    source: str
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class MemoryListResponse(BaseModel):
    """描述长期记忆列表响应。"""

    items: List[MemoryResponse]


@router.post("/memory", response_model=MemoryResponse)
def create_memory(
    request: MemoryCreateRequest,
    session: Session = Depends(get_db_session),
) -> MemoryResponse:
    """创建一条长期记忆，默认状态为 active。"""

    try:
        memory = MemoryStore(session).remember_preference(
            content=request.content,
            source=request.source,
            memory_type=request.memory_type,
            confidence=request.confidence,
            expires_at=request.expires_at,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return MemoryResponse.model_validate(memory)


@router.get("/memory", response_model=MemoryListResponse)
def list_memory(
    query: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db_session),
) -> MemoryListResponse:
    """查询 active 且未过期的长期记忆。"""

    try:
        memories = MemoryStore(session).search_memory(
            query=query,
            memory_type=memory_type,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return MemoryListResponse(items=[MemoryResponse.model_validate(memory) for memory in memories])


@router.patch("/memory/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: int,
    request: MemoryUpdateRequest,
    session: Session = Depends(get_db_session),
) -> MemoryResponse:
    """Update one long-term memory by ID."""

    updates = {
        field_name: getattr(request, field_name)
        for field_name in request.model_fields_set
    }
    try:
        memory = MemoryStore(session).update_memory(memory_id, updates)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if memory is None:
        raise HTTPException(status_code=404, detail="memory_not_found")
    return MemoryResponse.model_validate(memory)


@router.delete("/memory/{memory_id}", status_code=204)
def delete_memory(
    memory_id: int,
    session: Session = Depends(get_db_session),
) -> Response:
    """Soft-delete one long-term memory by ID."""

    memory = MemoryStore(session).delete_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="memory_not_found")
    return Response(status_code=204)
