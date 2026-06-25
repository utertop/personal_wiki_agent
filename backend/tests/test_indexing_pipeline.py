from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.db.base import Base
from app.indexing.pipeline import IndexingPipeline
from app.models.chunk import Chunk
from app.models.document import Document
from app.repositories.sources import SourceRepository


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def create_local_source(session, root, name="本地资料"):
    return SourceRepository(session).create(
        source_type="local_directory",
        name=name,
        uri=str(root),
        storage_mode="local_only",
        sync_direction="read_only",
    )


def test_pipeline_indexes_new_local_markdown_document(tmp_path) -> None:
    note = tmp_path / "rag.md"
    note.write_text("# RAG\n\n知识库内容", encoding="utf-8")
    session = make_session()
    source = create_local_source(session, tmp_path)

    job = IndexingPipeline(session).run_source_index(source.source_id)

    documents = session.query(Document).all()
    chunks = session.query(Chunk).all()
    assert job.status == "completed"
    assert job.total_items == 1
    assert job.processed_items == 1
    assert job.failed_items == 0
    assert len(documents) == 1
    assert documents[0].title == "rag"
    assert documents[0].metadata_json["mtime"] > 0
    assert len(chunks) == 1
    assert chunks[0].text == "知识库内容"
    assert chunks[0].heading_path == "RAG"


def test_pipeline_skips_unchanged_and_replaces_updated_chunks(tmp_path) -> None:
    note = tmp_path / "topic.md"
    note.write_text("# Topic\n\n旧内容", encoding="utf-8")
    session = make_session()
    source = create_local_source(session, tmp_path)
    pipeline = IndexingPipeline(session)

    first_job = pipeline.run_source_index(source.source_id)
    second_job = pipeline.run_source_index(source.source_id)
    note.write_text("# Topic\n\n新内容", encoding="utf-8")
    third_job = pipeline.run_source_index(source.source_id)

    documents = session.query(Document).all()
    chunks = session.query(Chunk).all()
    assert first_job.processed_items == 1
    assert second_job.processed_items == 0
    assert third_job.processed_items == 1
    assert len(documents) == 1
    assert len(chunks) == 1
    assert chunks[0].text == "新内容"


def test_pipeline_marks_missing_document_deleted(tmp_path) -> None:
    note = tmp_path / "remove.md"
    note.write_text("# Remove\n\n即将删除", encoding="utf-8")
    session = make_session()
    source = create_local_source(session, tmp_path)
    pipeline = IndexingPipeline(session)

    pipeline.run_source_index(source.source_id)
    note.unlink()
    job = pipeline.run_source_index(source.source_id)

    document = session.query(Document).one()
    assert job.status == "completed"
    assert job.total_items == 1
    assert job.processed_items == 1
    assert document.status == "deleted"


def test_pipeline_records_unsupported_file_failure_without_blocking_source(tmp_path) -> None:
    (tmp_path / "keep.md").write_text("# Keep\n\n可解析", encoding="utf-8")
    (tmp_path / "data.bin").write_bytes(b"binary")
    session = make_session()
    source = create_local_source(session, tmp_path)

    job = IndexingPipeline(session).run_source_index(source.source_id)

    assert job.status == "completed_with_errors"
    assert job.total_items == 2
    assert job.processed_items == 1
    assert job.failed_items == 1
    assert "unsupported_parser" in job.error_message
    assert session.query(Document).count() == 1
    assert session.query(Chunk).count() == 1


def test_pipeline_runs_all_enabled_sources(tmp_path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    (first_root / "a.txt").write_text("第一份资料", encoding="utf-8")
    (second_root / "b.txt").write_text("第二份资料", encoding="utf-8")
    session = make_session()
    create_local_source(session, first_root, name="资料一")
    create_local_source(session, second_root, name="资料二")

    jobs = IndexingPipeline(session).run_all_sources()

    assert len(jobs) == 2
    assert all(job.status == "completed" for job in jobs)
    assert session.query(Document).count() == 2
    assert session.query(Chunk).count() == 2
