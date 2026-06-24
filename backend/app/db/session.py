from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_session_factory(database_url: str):
    """根据数据库连接串创建 SQLAlchemy session 工厂。"""
    engine = create_engine(database_url)
    return sessionmaker(bind=engine)
