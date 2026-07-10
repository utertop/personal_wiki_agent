from alembic import op
import sqlalchemy as sa


revision = "0002_index_job_reliability"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add retry, heartbeat, and cancellation fields to index jobs."""
    op.add_column("index_jobs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("index_jobs", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("index_jobs", sa.Column("last_heartbeat_at", sa.DateTime(), nullable=True))
    op.add_column("index_jobs", sa.Column("cancel_requested_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove index job reliability fields."""
    op.drop_column("index_jobs", "cancel_requested_at")
    op.drop_column("index_jobs", "last_heartbeat_at")
    op.drop_column("index_jobs", "max_attempts")
    op.drop_column("index_jobs", "attempt_count")
