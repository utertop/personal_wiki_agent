from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import create_app


def make_client() -> TestClient:
    """创建共享内存数据库的 API 测试客户端。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    app = create_app()
    app.state.session_factory = session_factory
    return TestClient(app)


def test_sources_api_creates_and_lists_sources(tmp_path) -> None:
    """验证 Source API 可以创建本地数据源并按创建顺序列出。"""

    client = make_client()

    created = client.post(
        "/sources",
        json={
            "source_type": "local_directory",
            "name": "本地知识目录",
            "uri": str(tmp_path),
        },
    )
    listed = client.get("/sources")

    assert created.status_code == 200
    created_body = created.json()
    assert created_body["source_id"] >= 1
    assert created_body["source_type"] == "local_directory"
    assert created_body["storage_mode"] == "local_only"
    assert created_body["sync_direction"] == "read_only"
    assert created_body["enabled"] is True
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()["items"]] == ["本地知识目录"]


def test_sources_api_rejects_unsupported_source_type(tmp_path) -> None:
    """验证 Source API 拒绝当前没有 connector 的数据源类型。"""

    client = make_client()

    response = client.post(
        "/sources",
        json={
            "source_type": "cloud_notes",
            "name": "云端笔记",
            "uri": str(tmp_path),
        },
    )

    assert response.status_code == 422


def test_index_api_runs_source_and_lists_jobs(tmp_path) -> None:
    """验证 Index API 会先返回排队任务，再由后台任务完成索引并写入搜索结果。"""

    note = tmp_path / "rag.md"
    note.write_text("# RAG\n\nRAG personal wiki content", encoding="utf-8")
    client = make_client()
    source = client.post(
        "/sources",
        json={
            "source_type": "local_directory",
            "name": "索引资料",
            "uri": str(tmp_path),
        },
    ).json()

    run_response = client.post("/index/run", json={"source_id": source["source_id"]})
    jobs_response = client.get("/index/jobs")
    search_response = client.post("/search", json={"query": "RAG", "top_k": 5})

    assert run_response.status_code == 202
    run_body = run_response.json()
    assert len(run_body["jobs"]) == 1
    assert run_body["jobs"][0]["status"] == "queued"
    assert run_body["jobs"][0]["processed_items"] == 0
    assert jobs_response.status_code == 200
    assert jobs_response.json()["items"][0]["source_name"] == "索引资料"
    assert jobs_response.json()["items"][0]["status"] == "completed"
    assert search_response.status_code == 200
    assert search_response.json()["results"][0]["document"]["title"] == "rag"


def test_index_api_runs_all_enabled_sources(tmp_path) -> None:
    """验证 Index API 不指定 source_id 时会为全部启用数据源创建后台索引任务。"""

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "a.txt").write_text("第一份资料", encoding="utf-8")
    (second / "b.txt").write_text("第二份资料", encoding="utf-8")
    client = make_client()
    client.post("/sources", json={"source_type": "local_directory", "name": "第一目录", "uri": str(first)})
    client.post("/sources", json={"source_type": "local_directory", "name": "第二目录", "uri": str(second)})

    response = client.post("/index/run", json={})

    assert response.status_code == 202
    body = response.json()
    assert len(body["jobs"]) == 2
    assert {job["status"] for job in body["jobs"]} == {"queued"}
    assert {job["source_name"] for job in body["jobs"]} == {"第一目录", "第二目录"}


def test_index_api_returns_404_for_missing_source() -> None:
    """验证触发不存在的数据源索引时返回 404，而不是创建失败任务。"""

    client = make_client()

    response = client.post("/index/run", json={"source_id": 9999})

    assert response.status_code == 404
