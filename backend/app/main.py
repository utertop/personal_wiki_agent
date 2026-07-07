import os
from pathlib import Path
from typing import Mapping, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.api.routes_index import router as index_router
from app.api.routes_memory import router as memory_router
from app.api.routes_search import router as search_router
from app.api.routes_sources import router as sources_router
from app.core.settings import AppSettings, load_settings
from app.llm.bootstrap import build_model_router


LOCAL_WEB_UI_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

CONFIG_PATH_ENV = "PERSONAL_WIKI_CONFIG_PATH"


def create_app(
    settings: Optional[AppSettings] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> FastAPI:
    """创建 FastAPI 应用实例，并集中注册后端 API 路由。"""
    resolved_environ = environ or os.environ
    resolved_settings = settings or load_settings(_config_path_from_environ(resolved_environ))
    app = FastAPI(title="Personal Wiki Agent API")
    app.state.settings = resolved_settings
    model_router = build_model_router(resolved_settings, resolved_environ)
    if model_router is not None:
        app.state.model_router = model_router
    configure_cors(app)
    app.include_router(health_router)
    app.include_router(search_router)
    app.include_router(documents_router)
    app.include_router(sources_router)
    app.include_router(index_router)
    app.include_router(memory_router)
    app.include_router(chat_router)
    return app


def _config_path_from_environ(environ: Mapping[str, str]) -> Optional[Path]:
    """Resolve the optional YAML config path from the process environment."""

    raw_path = environ.get(CONFIG_PATH_ENV, "").strip()
    return Path(raw_path) if raw_path else None


def configure_cors(app: FastAPI) -> None:
    """允许本地 Web UI 在开发模式下跨端口调用后端 API。"""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_WEB_UI_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app = create_app()
