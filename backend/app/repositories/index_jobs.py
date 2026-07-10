from datetime import timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.index_job import IndexJob


class IndexJobRepository:
    """封装 IndexJob 表的状态流转和统计写入。"""

    def __init__(self, session: Session) -> None:
        """保存当前索引任务使用的数据库 session。"""
        self.session = session

    def create(self, source_id: int, status: str = "running", max_attempts: int = 3) -> IndexJob:
        """创建一个索引任务记录；API 后台任务先写入 queued，流水线直跑时写入 running。"""
        now = utc_now()
        job = IndexJob(
            source_id=source_id,
            status=status,
            started_at=now if status == "running" else None,
            total_items=0,
            processed_items=0,
            failed_items=0,
            attempt_count=0,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def mark_running(self, job_id: int) -> IndexJob:
        """把已排队任务切换为 running，并记录实际开始执行时间。"""
        job = self.session.get(IndexJob, job_id)
        now = utc_now()
        job.status = "running"
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        job.last_heartbeat_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

    def get(self, job_id: int) -> Optional[IndexJob]:
        """按主键查询索引任务；不存在时返回 None。"""
        return self.session.get(IndexJob, job_id)

    def touch_heartbeat(self, job_id: int) -> IndexJob:
        """Update the last heartbeat timestamp for a running job."""
        job = self.session.get(IndexJob, job_id)
        now = utc_now()
        job.last_heartbeat_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

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
        job.updated_at = utc_now()
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
        now = utc_now()
        job.status = status
        job.total_items = total_items
        job.processed_items = processed_items
        job.failed_items = failed_items
        job.error_message = "\n".join(errors) if errors else None
        job.finished_at = now
        job.last_heartbeat_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

    def mark_failed(self, job_id: int, error_message: str) -> IndexJob:
        """在 source 级异常时把任务标记为 failed。"""
        job = self.session.get(IndexJob, job_id)
        now = utc_now()
        job.status = "failed"
        job.failed_items = max(job.failed_items, 1)
        job.error_message = error_message
        job.finished_at = now
        job.last_heartbeat_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

    def request_cancel(self, job_id: int) -> Optional[IndexJob]:
        """Cancel a queued or running job and record when cancellation was requested."""
        job = self.session.get(IndexJob, job_id)
        if job is None:
            return None
        now = utc_now()
        job.status = "cancelled"
        job.cancel_requested_at = now
        job.finished_at = now
        job.updated_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

    def retry_failed(self, job_id: int) -> Optional[IndexJob]:
        """Re-queue a failed job if it has remaining attempts."""
        job = self.session.get(IndexJob, job_id)
        if job is None or job.status != "failed" or job.attempt_count >= job.max_attempts:
            return None
        job.status = "queued"
        job.finished_at = None
        job.error_message = None
        job.cancel_requested_at = None
        job.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(job)
        return job

    def recover_stale_running_jobs(self, stale_after: timedelta) -> List[IndexJob]:
        """Requeue stale running jobs while attempts remain; otherwise mark them failed."""
        cutoff = utc_now() - stale_after
        stale_jobs = (
            self.session.query(IndexJob)
            .filter(IndexJob.status == "running")
            .filter(IndexJob.last_heartbeat_at.is_not(None))
            .filter(IndexJob.last_heartbeat_at < cutoff)
            .order_by(IndexJob.job_id)
            .all()
        )
        now = utc_now()
        for job in stale_jobs:
            if job.attempt_count >= job.max_attempts:
                job.status = "failed"
                job.error_message = "stale_running_job_exhausted"
                job.finished_at = now
            else:
                job.status = "queued"
                job.error_message = "stale_running_job_requeued"
                job.finished_at = None
            job.updated_at = now
        self.session.commit()
        for job in stale_jobs:
            self.session.refresh(job)
        return stale_jobs

    def list_recent(self, limit: int = 50) -> List[IndexJob]:
        """按更新时间倒序列出最近索引任务，供 API 和前端状态页展示。"""

        return (
            self.session.query(IndexJob)
            .order_by(IndexJob.updated_at.desc(), IndexJob.job_id.desc())
            .limit(limit)
            .all()
        )
