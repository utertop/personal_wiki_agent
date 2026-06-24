from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 MVP 初始 schema，包括数据源、文档、chunk、任务和长期记忆表。"""
    op.create_table(
        "sources",
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("uri", sa.String(length=1024), nullable=False),
        sa.Column("storage_mode", sa.String(length=64), nullable=False),
        sa.Column("sync_direction", sa.String(length=64), nullable=False),
        sa.Column("config_hash", sa.String(length=128), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
    )
    op.create_index(op.f("ix_sources_source_id"), "sources", ["source_id"], unique=False)
    op.create_index(op.f("ix_sources_source_type"), "sources", ["source_type"], unique=False)

    op.create_table(
        "documents",
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("uri", sa.String(length=1024), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("remote_id", sa.String(length=255), nullable=True),
        sa.Column("mirror_status", sa.String(length=64), nullable=True),
        sa.Column("mirror_uri", sa.String(length=1024), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("indexed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.source_id"]),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index(op.f("ix_documents_content_hash"), "documents", ["content_hash"], unique=False)
    op.create_index(op.f("ix_documents_document_id"), "documents", ["document_id"], unique=False)
    op.create_index(op.f("ix_documents_remote_id"), "documents", ["remote_id"], unique=False)
    op.create_index(op.f("ix_documents_source_id"), "documents", ["source_id"], unique=False)

    op.create_table(
        "index_jobs",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("processed_items", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.source_id"]),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(op.f("ix_index_jobs_job_id"), "index_jobs", ["job_id"], unique=False)
    op.create_index(op.f("ix_index_jobs_source_id"), "index_jobs", ["source_id"], unique=False)

    op.create_table(
        "memories",
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("memory_id"),
    )
    op.create_index(op.f("ix_memories_memory_id"), "memories", ["memory_id"], unique=False)
    op.create_index(op.f("ix_memories_memory_type"), "memories", ["memory_type"], unique=False)

    op.create_table(
        "chunks",
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("heading_path", sa.String(length=1024), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.document_id"]),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index(op.f("ix_chunks_chunk_id"), "chunks", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_chunks_document_id"), "chunks", ["document_id"], unique=False)


def downgrade() -> None:
    """回滚 MVP 初始 schema，按外键依赖反向删除核心表。"""
    op.drop_index(op.f("ix_chunks_document_id"), table_name="chunks")
    op.drop_index(op.f("ix_chunks_chunk_id"), table_name="chunks")
    op.drop_table("chunks")

    op.drop_index(op.f("ix_memories_memory_type"), table_name="memories")
    op.drop_index(op.f("ix_memories_memory_id"), table_name="memories")
    op.drop_table("memories")

    op.drop_index(op.f("ix_index_jobs_source_id"), table_name="index_jobs")
    op.drop_index(op.f("ix_index_jobs_job_id"), table_name="index_jobs")
    op.drop_table("index_jobs")

    op.drop_index(op.f("ix_documents_source_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_remote_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_content_hash"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_sources_source_type"), table_name="sources")
    op.drop_index(op.f("ix_sources_source_id"), table_name="sources")
    op.drop_table("sources")
