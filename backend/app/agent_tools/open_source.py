from typing import Optional, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.routes_documents import (
    ChunkDetailResponse,
    DocumentDetailResponse,
    get_chunk_detail,
    get_document_detail,
)


def open_source(
    session: Session,
    document_id: Optional[int] = None,
    chunk_id: Optional[int] = None,
) -> Union[DocumentDetailResponse, ChunkDetailResponse]:
    """为 Agent 打开文档或 chunk 来源，调用方无需直接访问 repository。"""
    if (document_id is None and chunk_id is None) or (document_id is not None and chunk_id is not None):
        raise ValueError("必须且只能提供 document_id 或 chunk_id。")

    try:
        if document_id is not None:
            return get_document_detail(document_id=document_id, session=session)
        return get_chunk_detail(chunk_id=chunk_id, session=session)
    except HTTPException as error:
        raise ValueError(str(error.detail)) from error
