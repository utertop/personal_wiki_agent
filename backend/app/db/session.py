from typing import Iterator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import load_settings


_DEFAULT_SESSION_FACTORY = None


def create_session_factory(database_url: str):
    """根据数据库连接串创建 SQLAlchemy session 工厂。"""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    return sessionmaker(bind=engine)


def get_db_session(request: Request) -> Iterator[Session]:
    """为 FastAPI 请求提供数据库 session；测试可通过 app.state 注入 session_factory。"""
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        session_factory = _get_default_session_factory()

    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _get_default_session_factory():
    """延迟创建默认数据库连接，避免导入模块时立即触碰本地数据目录。"""
    global _DEFAULT_SESSION_FACTORY
    if _DEFAULT_SESSION_FACTORY is None:
        settings = load_settings(None)
        _DEFAULT_SESSION_FACTORY = create_session_factory(settings.database_url)
    return _DEFAULT_SESSION_FACTORY
