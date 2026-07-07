import os
from pathlib import Path
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.settings import AppSettings, ModelConfig, ModelInfoConfig, ProviderSettings
from app.db.base import Base
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.main import create_app
from app.repositories.documents import DocumentRepository
from app.repositories.sources import SourceRepository


def test_real_openai_compatible_chat_smoke() -> None:
    """显式开启后，用真实 OpenAI-compatible provider 跑通 Chat API 最小闭环。"""

    env = _smoke_environ()
    api_key_env = env.get("PERSONAL_WIKI_SMOKE_API_KEY_ENV", "PERSONAL_WIKI_NVIDIA_API_KEY")
    if env.get("PERSONAL_WIKI_ENABLE_REAL_MODEL_SMOKE") != "1":
        pytest.skip("set PERSONAL_WIKI_ENABLE_REAL_MODEL_SMOKE=1 to run real model smoke test")
    if not env.get(api_key_env):
        pytest.skip(f"set {api_key_env} in environment or frontend/.env.local")

    app = create_app(settings=_smoke_settings(env), environ=env)
    session_factory = _seed_indexed_knowledge(app)
    app.state.session_factory = session_factory
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"message": "RAG 怎么帮助个人知识库？请用一句中文回答。", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].strip()
    assert body["citations"]
    assert body["model"] == f"{_smoke_provider_id(env)}/{_smoke_model_id(env)}"
    assert body["retrieval_summary"]["has_reliable_sources"] is True


def _smoke_environ() -> Dict[str, str]:
    """Merge process environment with optional non-secret-printing dotenv values."""

    env = dict(os.environ)
    env.update(_read_dotenv(_repo_root() / "frontend" / ".env.local"))
    return env


def _read_dotenv(path: Path) -> Dict[str, str]:
    """Read simple KEY=VALUE dotenv lines without logging secrets."""

    if not path.exists():
        return {}

    values: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _smoke_settings(env: Dict[str, str]) -> AppSettings:
    """Build runtime settings for a real provider smoke test."""

    provider_id = _smoke_provider_id(env)
    model_id = _smoke_model_id(env)
    base_url = env.get("PERSONAL_WIKI_SMOKE_BASE_URL", "https://integrate.api.nvidia.com/v1")
    api_key_env = env.get("PERSONAL_WIKI_SMOKE_API_KEY_ENV", "PERSONAL_WIKI_NVIDIA_API_KEY")
    return AppSettings(
        model=ModelConfig(
            providers={
                provider_id: ProviderSettings(
                    type="openai_compatible",
                    base_url=base_url,
                    api_key_env=api_key_env,
                    models=[
                        ModelInfoConfig(
                            id=model_id,
                            display_name="Smoke Test Chat Model",
                            capabilities=["chat"],
                        )
                    ],
                )
            },
            defaults={"chat": f"{provider_id}/{model_id}"},
        )
    )


def _smoke_provider_id(env: Dict[str, str]) -> str:
    """Return provider id used by the smoke test router."""

    return env.get("PERSONAL_WIKI_SMOKE_PROVIDER_ID", "nvidia")


def _smoke_model_id(env: Dict[str, str]) -> str:
    """Return model id sent to the OpenAI-compatible provider."""

    return env.get("PERSONAL_WIKI_SMOKE_MODEL", "meta/llama-3.1-70b-instruct")


def _seed_indexed_knowledge(app) -> sessionmaker:
    """Create an in-memory knowledge base with one searchable RAG note."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    source = SourceRepository(session).create(
        source_type="local_directory",
        name="Smoke Notes",
        uri="E:/Knowledge",
        storage_mode="local_only",
        sync_direction="read_only",
    )
    repository = DocumentRepository(session)
    document = repository.create_document(
        source_id=source.source_id,
        uri="E:/Knowledge/rag.md",
        title="RAG 笔记",
        content_hash="smoke-rag",
        mime_type="text/markdown",
        metadata_json={"relative_path": "rag.md", "source_format": "markdown"},
    )
    chunk = repository.create_chunk(
        document_id=document.document_id,
        chunk_index=0,
        text="RAG 可以先检索个人知识库里的本地资料，再把相关片段交给模型生成带来源引用的回答。",
        heading_path="RAG / 个人知识库",
        page_number=1,
        token_count=36,
        metadata_json={"source_format": "markdown"},
    )
    SQLiteFtsIndex(session).index_chunks([chunk])
    session.close()
    return session_factory


def _repo_root() -> Path:
    """Return repository root from this test file."""

    return Path(__file__).resolve().parents[2]
