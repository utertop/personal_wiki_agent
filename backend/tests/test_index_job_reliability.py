from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.time import utc_now
from app.db.base import Base
from app.models.index_job import IndexJob
from app.repositories.index_jobs import IndexJobRepository
from app.repositories.sources import SourceRepository


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def create_source(session):
    return SourceRepository(session).create(
        source_type="local_directory",
        name="Index Reliability Source",
        uri="E:/Knowledge",
        storage_mode="local_only",
        sync_direction="read_only",
    )


def test_index_job_repository_tracks_attempts_and_heartbeat() -> None:
    session = make_session()
    source = create_source(session)
    repository = IndexJobRepository(session)
    job = repository.create(source_id=source.source_id, status="queued", max_attempts=2)

    running = repository.mark_running(job.job_id)
    before_touch = running.last_heartbeat_at
    touched = repository.touch_heartbeat(job.job_id)

    assert running.status == "running"
    assert running.attempt_count == 1
    assert running.max_attempts == 2
    assert before_touch is not None
    assert touched.last_heartbeat_at >= before_touch


def test_index_job_repository_cancels_queued_and_running_jobs() -> None:
    session = make_session()
    source = create_source(session)
    repository = IndexJobRepository(session)
    queued = repository.create(source_id=source.source_id, status="queued")
    running = repository.mark_running(repository.create(source_id=source.source_id, status="queued").job_id)

    cancelled_queued = repository.request_cancel(queued.job_id)
    cancelled_running = repository.request_cancel(running.job_id)

    assert cancelled_queued.status == "cancelled"
    assert cancelled_queued.cancel_requested_at is not None
    assert cancelled_queued.finished_at is not None
    assert cancelled_running.status == "cancelled"
    assert cancelled_running.cancel_requested_at is not None


def test_index_job_repository_retries_failed_job_until_max_attempts() -> None:
    session = make_session()
    source = create_source(session)
    repository = IndexJobRepository(session)
    job = repository.create(source_id=source.source_id, status="queued", max_attempts=2)
    repository.mark_running(job.job_id)
    failed = repository.mark_failed(job.job_id, "boom")

    retried = repository.retry_failed(failed.job_id)
    assert retried.status == "queued"
    assert retried.error_message is None
    assert retried.finished_at is None

    repository.mark_running(retried.job_id)
    repository.mark_failed(retried.job_id, "boom again")
    exhausted = repository.retry_failed(retried.job_id)

    assert exhausted is None


def test_index_job_repository_recovers_stale_running_jobs() -> None:
    session = make_session()
    source = create_source(session)
    repository = IndexJobRepository(session)
    stale = repository.mark_running(repository.create(source_id=source.source_id, status="queued").job_id)
    exhausted = repository.mark_running(
        repository.create(source_id=source.source_id, status="queued", max_attempts=1).job_id
    )
    fresh = repository.mark_running(repository.create(source_id=source.source_id, status="queued").job_id)
    old_time = utc_now() - timedelta(minutes=30)
    session.query(IndexJob).filter(IndexJob.job_id.in_([stale.job_id, exhausted.job_id])).update(
        {IndexJob.last_heartbeat_at: old_time},
        synchronize_session=False,
    )
    session.commit()

    recovered = repository.recover_stale_running_jobs(stale_after=timedelta(minutes=10))

    assert {job.job_id for job in recovered} == {stale.job_id, exhausted.job_id}
    assert repository.get(stale.job_id).status == "queued"
    assert repository.get(exhausted.job_id).status == "failed"
    assert repository.get(fresh.job_id).status == "running"
