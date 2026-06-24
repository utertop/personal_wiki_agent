from fastapi import FastAPI

from app.api.routes_health import router as health_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例，并集中注册后端 API 路由。"""
    app = FastAPI(title="Personal Wiki Agent API")
    app.include_router(health_router)
    return app


app = create_app()
