from fastapi.testclient import TestClient

from app.core.settings import AppSettings, ModelConfig, ModelInfoConfig, ProviderSettings
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
