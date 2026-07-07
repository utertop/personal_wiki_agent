import os

import pytest
from fastapi.testclient import TestClient

from app.core.settings import AppSettings, ModelConfig, ModelInfoConfig, ProviderSettings
from app.main import create_app
from tests.test_real_model_smoke import _seed_indexed_knowledge


def test_local_ollama_chat_smoke() -> None:
    """显式开启后，用本地 Ollama 跑通 Chat API 最小闭环。"""

    if os.environ.get("PERSONAL_WIKI_ENABLE_OLLAMA_SMOKE") != "1":
        pytest.skip("set PERSONAL_WIKI_ENABLE_OLLAMA_SMOKE=1 to run local Ollama smoke test")

    model_id = os.environ.get("PERSONAL_WIKI_OLLAMA_MODEL", "qwen3")
    base_url = os.environ.get("PERSONAL_WIKI_OLLAMA_BASE_URL", "http://localhost:11434")
    app = create_app(
        settings=AppSettings(
            model=ModelConfig(
                providers={
                    "ollama": ProviderSettings(
                        type="ollama",
                        base_url=base_url,
                        models=[
                            ModelInfoConfig(
                                id=model_id,
                                display_name="Local Ollama Chat",
                                capabilities=["chat", "local"],
                                local=True,
                            )
                        ],
                    )
                },
                defaults={"chat": f"ollama/{model_id}"},
            )
        )
    )
    app.state.session_factory = _seed_indexed_knowledge(app)
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"message": "RAG 怎么帮助个人知识库？请用一句中文回答。", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].strip()
    assert body["citations"]
    assert body["model"] == f"ollama/{model_id}"
    assert body["retrieval_summary"]["has_reliable_sources"] is True
