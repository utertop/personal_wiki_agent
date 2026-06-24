from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health() -> Dict[str, str]:
    return {"status": "ok"}
