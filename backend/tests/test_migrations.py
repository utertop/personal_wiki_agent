from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def make_alembic_config(database_url: str) -> Config:
    """构造指向测试数据库的 Alembic 配置。"""

    repo_root = Path(__file__).resolve().parents[2]
    config = Config(str(repo_root / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(repo_root / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_alembic_upgrade_creates_core_tables(tmp_path) -> None:
    """验证 Alembic upgrade 会创建核心业务表。"""

    database_path = tmp_path / "test.db"
    database_url = "sqlite:///" + database_path.as_posix()
    config = make_alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    table_names = set(inspect(engine).get_table_names())

    assert {
        "sources",
        "documents",
        "chunks",
        "index_jobs",
        "memories",
        "alembic_version",
    }.issubset(table_names)


def test_alembic_downgrade_base_removes_core_tables(tmp_path) -> None:
    """验证 Alembic downgrade 到 base 会移除核心业务表。"""

    database_path = tmp_path / "test.db"
    database_url = "sqlite:///" + database_path.as_posix()
    config = make_alembic_config(database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(database_url)
    table_names = set(inspect(engine).get_table_names())

    assert {
        "sources",
        "documents",
        "chunks",
        "index_jobs",
        "memories",
    }.isdisjoint(table_names)
