from fastapi import FastAPI

from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.api.routes_index import router as index_router
from app.api.routes_memory import router as memory_router
from app.api.routes_search import router as search_router
from app.api.routes_sources import router as sources_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例，并集中注册后端 API 路由。"""
    app = FastAPI(title="Personal Wiki Agent API")
    app.include_router(health_router)
    app.include_router(search_router)
    app.include_router(documents_router)
    app.include_router(sources_router)
    app.include_router(index_router)
    app.include_router(memory_router)
    app.include_router(chat_router)
    return app


app = create_app()
