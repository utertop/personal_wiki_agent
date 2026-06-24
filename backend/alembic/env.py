from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.db.base import Base  # noqa: E402
from app import models  # noqa: F401,E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """以离线模式生成迁移 SQL，不直接连接数据库。"""
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """以在线模式连接数据库并执行 Alembic 迁移。"""
    config_section = context.config.get_section(context.config.config_ini_section)
    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
