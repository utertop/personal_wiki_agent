from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health() -> Dict[str, str]:
    """返回服务健康状态，用于本地启动、测试和后续部署探针。"""
    return {"status": "ok"}
