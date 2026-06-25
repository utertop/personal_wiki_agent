from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok_status() -> None:
    """验证健康检查接口返回可用状态。"""

    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
