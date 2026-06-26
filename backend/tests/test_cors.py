from fastapi.testclient import TestClient

from app.main import create_app


def test_cors_allows_vite_dev_origin() -> None:
    """验证本地 Vite Web UI 可以跨端口访问 FastAPI API。"""

    client = TestClient(create_app())

    response = client.options(
        "/sources",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "POST" in response.headers["access-control-allow-methods"]
