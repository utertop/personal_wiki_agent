from fastapi.testclient import TestClient

from app.core.settings import AppSettings, ModelConfig, ModelInfoConfig, ProviderSettings, VectorStoreConfig
from app.indexing.embedding import ProviderEmbeddingAdapter
from app.indexing.vector_store import SQLiteVectorStore
from app.main import create_app


def test_create_app_mounts_model_router_from_settings_and_environment() -> None:
    """验证应用启动时会根据模型配置和环境变量挂载 ModelRouter。"""

    settings = AppSettings(
        model=ModelConfig(
            providers={
                "openai": ProviderSettings(
                    type="openai_compatible",
                    base_url="https://api.openai.example/v1",
                    api_key_env="OPENAI_API_KEY",
                    models=[
                        ModelInfoConfig(
                            id="chat-model",
                            display_name="Chat Model",
                            capabilities=["chat"],
                        )
                    ],
                )
            },
            defaults={"chat": "openai/chat-model"},
        )
    )

    app = create_app(settings=settings, environ={"OPENAI_API_KEY": "sk-test"})

    client = TestClient(app)
    assert client.get("/health").status_code == 200
    selection = app.state.model_router.select_model("chat")
    assert selection.full_name == "openai/chat-model"
    assert selection.provider.validate_credentials().ok is True


def test_create_app_loads_model_router_from_config_path_environment(tmp_path) -> None:
    """验证默认启动路径可通过环境变量读取配置文件并挂载 ModelRouter。"""

    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        """
model:
  providers:
    openai:
      type: openai_compatible
      base_url: https://api.openai.example/v1
      api_key_env: OPENAI_API_KEY
      models:
        - id: chat-model
          display_name: Chat Model
          capabilities:
            - chat
  defaults:
    chat: openai/chat-model
""".strip(),
        encoding="utf-8",
    )

    app = create_app(
        environ={
            "PERSONAL_WIKI_CONFIG_PATH": str(config_path),
            "OPENAI_API_KEY": "sk-test",
        }
    )

    assert app.state.settings.model.providers["openai"].base_url == "https://api.openai.example/v1"
    assert app.state.model_router.select_model("chat").full_name == "openai/chat-model"


def test_create_app_mounts_configured_embedding_and_vector_store(tmp_path) -> None:
    """Verify app startup wires real embedding and persistent vector dependencies from settings."""

    settings = AppSettings(
        data_dir=tmp_path,
        vector_store=VectorStoreConfig(
            enabled=True,
            provider="sqlite",
            path=tmp_path / "semantic" / "vectors.sqlite3",
        ),
        model=ModelConfig(
            providers={
                "openai": ProviderSettings(
                    type="openai_compatible",
                    base_url="https://api.openai.example/v1",
                    api_key_env="OPENAI_API_KEY",
                    models=[
                        ModelInfoConfig(
                            id="embedding-model",
                            display_name="Embedding Model",
                            capabilities=["embedding"],
                            embedding_dimensions=3,
                        )
                    ],
                )
            },
            defaults={"embedding": "openai/embedding-model"},
        ),
    )

    app = create_app(settings=settings, environ={"OPENAI_API_KEY": "sk-test"})

    assert isinstance(app.state.embedder, ProviderEmbeddingAdapter)
    assert isinstance(app.state.vector_store, SQLiteVectorStore)


def test_create_app_leaves_vector_dependencies_unset_by_default() -> None:
    """Verify the default app keeps semantic search disabled unless vector_store is enabled."""

    app = create_app(settings=AppSettings(), environ={})

    assert not hasattr(app.state, "embedder")
    assert not hasattr(app.state, "vector_store")
