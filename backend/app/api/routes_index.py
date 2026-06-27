from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import create_session_factory
from app.db.session import get_db_session
from app.indexing.pipeline import IndexingPipeline
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.models.index_job import IndexJob
from app.repositories.index_jobs import IndexJobRepository
from app.repositories.sources import SourceRepository


router = APIRouter(tags=["index"])


class IndexRunRequest(BaseModel):
    """描述触发索引任务的 API 入参；不传 source_id 时索引全部启用 source。"""

    model_config = ConfigDict(extra="forbid")

    source_id: Optional[int] = Field(default=None, ge=1)


class IndexJobResponse(BaseModel):
    """描述 API 返回的一条索引任务状态。"""

    job_id: int
    source_id: int
    source_name: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_items: int
    processed_items: int
    failed_items: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IndexJobListResponse(BaseModel):
    """描述索引任务列表响应。"""

    items: List[IndexJobResponse]


class IndexRunResponse(BaseModel):
    """描述一次索引触发返回的任务集合。"""

    jobs: List[IndexJobResponse]


@router.post("/index/run", response_model=IndexRunResponse, status_code=status.HTTP_202_ACCEPTED)
def run_index(
    request: IndexRunRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    session: Session = Depends(get_db_session),
) -> IndexRunResponse:
    """排队触发索引任务，并把实际索引执行交给 FastAPI 后台任务。"""

    sources = SourceRepository(session)
    if request.source_id is not None and sources.get(request.source_id) is None:
        raise HTTPException(status_code=404, detail="source_not_found")

    if request.source_id is not None:
        target_source_ids = [request.source_id]
    else:
        target_source_ids = [source.source_id for source in sources.list_enabled()]

    job_repository = IndexJobRepository(session)
    jobs = [
        job_repository.create(source_id=source_id, status="queued")
        for source_id in target_source_ids
    ]
    background_tasks.add_task(
        run_queued_index_jobs,
        _session_factory_for_background(http_request),
        [(job.source_id, job.job_id) for job in jobs],
    )

    source_names = _source_names(session)
    return IndexRunResponse(jobs=[_job_response(job, source_names) for job in jobs])


@router.get("/index/jobs", response_model=IndexJobListResponse)
def list_index_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> IndexJobListResponse:
    """列出最近索引任务，供前端索引状态页展示。"""

    jobs = IndexJobRepository(session).list_recent(limit=limit)
    source_names = _source_names(session)
    return IndexJobListResponse(items=[_job_response(job, source_names) for job in jobs])


def _source_names(session: Session) -> Dict[int, str]:
    """读取 source_id 到 source 名称的映射，避免响应中只显示数字 ID。"""

    return {
        source.source_id: source.name
        for source in SourceRepository(session).list_all()
    }


def _job_response(job: IndexJob, source_names: Dict[int, str]) -> IndexJobResponse:
    """把 IndexJob ORM 对象转换为稳定的 API 响应模型。"""

    return IndexJobResponse(
        job_id=job.job_id,
        source_id=job.source_id,
        source_name=source_names.get(job.source_id),
        status=job.status,
        started_at=job.started_at,
        finished_at=job.finished_at,
        total_items=job.total_items,
        processed_items=job.processed_items,
        failed_items=job.failed_items,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _session_factory_for_background(request: Request):
    """读取后台索引使用的 session factory，确保后台任务不复用请求 session。"""
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is not None:
        return session_factory

    database_url = getattr(request.app.state, "database_url", None)
    if database_url is not None:
        return create_session_factory(database_url)

    # 导入默认 session factory 的路径集中在 get_db_session 内部；这里通过默认配置重建即可。
    from app.core.settings import load_settings

    return create_session_factory(load_settings(None).database_url)


def run_queued_index_jobs(session_factory: sessionmaker, job_specs: List[Tuple[int, int]]) -> None:
    """在后台任务中逐个执行已排队索引任务，并为每个任务使用独立数据库 session。"""
    for source_id, job_id in job_specs:
        session = session_factory()
        try:
            pipeline = IndexingPipeline(session, lexical_index=SQLiteFtsIndex(session))
            pipeline.run_source_index(source_id, job_id=job_id)
        finally:
            session.close()
