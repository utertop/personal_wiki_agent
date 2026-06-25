from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.index_job import IndexJob


class IndexJobRepository:
    """封装 IndexJob 表的状态流转和统计写入。"""

    def __init__(self, session: Session) -> None:
        """保存当前索引任务使用的数据库 session。"""
        self.session = session

    def create(self, source_id: int) -> IndexJob:
        """创建一个运行中的索引任务记录。"""
        now = datetime.utcnow()
        job = IndexJob(
            source_id=source_id,
            status="running",
            started_at=now,
            total_items=0,
            processed_items=0,
            failed_items=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get(self, job_id: int) -> Optional[IndexJob]:
        """按主键查询索引任务；不存在时返回 None。"""
        return self.session.get(IndexJob, job_id)

    def update_counts(
        self,
        job_id: int,
        total_items: int,
        processed_items: int,
        failed_items: int,
    ) -> IndexJob:
        """更新任务的处理总量、成功数量和失败数量。"""
        job = self.session.get(IndexJob, job_id)
        job.total_items = total_items
        job.processed_items = processed_items
        job.failed_items = failed_items
        job.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(job)
        return job

    def finish(
        self,
        job_id: int,
        status: str,
        total_items: int,
        processed_items: int,
        failed_items: int,
        errors: List[str],
    ) -> IndexJob:
        """结束索引任务，并保存最终状态、统计和错误摘要。"""
        job = self.session.get(IndexJob, job_id)
        now = datetime.utcnow()
        job.status = status
        job.total_items = total_items
        job.processed_items = processed_items
        job.failed_items = failed_items
        job.error_message = "\n".join(errors) if errors else None
        job.finished_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

    def mark_failed(self, job_id: int, error_message: str) -> IndexJob:
        """在 source 级异常时把任务标记为 failed。"""
        job = self.session.get(IndexJob, job_id)
        now = datetime.utcnow()
        job.status = "failed"
        job.failed_items = max(job.failed_items, 1)
        job.error_message = error_message
        job.finished_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job
