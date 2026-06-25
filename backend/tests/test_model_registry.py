import pytest

from app.llm.catalog import ModelCatalog
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.provider import (
    ModelInfo,
    ProviderConfig,
    ProviderConfigurationError,
)
from app.llm.registry import ModelRegistry, provider_from_config
from app.llm.router import ModelRouter, ModelRoutingError


def test_openai_compatible_provider_validates_api_key_and_lists_configured_models() -> None:
    """验证 OpenAI 兼容 Provider 会校验密钥并暴露配置中的模型。"""

    missing_key = OpenAICompatibleProvider(
        ProviderConfig(
            provider_id="openai",
            provider_type="openai_compatible",
            base_url="https://api.openai.example/v1",
            models=[],
        )
    )
    configured = OpenAICompatibleProvider(
        ProviderConfig(
            provider_id="openai",
            provider_type="openai_compatible",
            base_url="https://api.openai.example/v1",
            api_key="sk-test",
            models=[
                ModelInfo(
                    provider_id="openai",
                    model_id="chat-model",
                    display_name="Chat Model",
                    capabilities=["chat", "summary"],
                ),
                ModelInfo(
                    provider_id="openai",
                    model_id="embedding-model",
                    display_name="Embedding Model",
                    capabilities=["embedding"],
                    embedding_dimensions=1536,
                ),
            ],
        )
    )

    missing_status = missing_key.validate_credentials()
    configured_status = configured.validate_credentials()
    models = configured.list_models()

    assert missing_status.ok is False
    assert missing_status.reason == "missing_api_key"
    assert configured_status.ok is True
    assert [model.full_name for model in models] == [
        "openai/chat-model",
        "openai/embedding-model",
    ]
    assert configured.get_chat_client("chat-model").model_id == "chat-model"
    assert configured.get_embedding_client("embedding-model").model_id == "embedding-model"


def test_ollama_provider_uses_local_config_without_api_key() -> None:
    """验证 Ollama Provider 使用本地配置且不要求 API Key。"""

    provider = OllamaProvider(
        ProviderConfig(
            provider_id="ollama",
            provider_type="ollama",
            base_url="http://localhost:11434",
            models=[
                ModelInfo(
                    provider_id="ollama",
                    model_id="qwen3",
                    display_name="Qwen Local",
                    capabilities=["chat", "local"],
                    local=True,
                )
            ],
        )
    )

    status = provider.validate_credentials()
    models = provider.list_models()

    assert status.ok is True
    assert provider.protocol == "ollama"
    assert provider.get_chat_client("qwen3").base_url == "http://localhost:11434"
    assert models[0].local is True


def test_model_registry_refreshes_catalog_from_registered_providers() -> None:
    """验证模型注册表可以从已注册 Provider 刷新模型目录。"""

    registry = ModelRegistry()
    registry.register_provider(
        OpenAICompatibleProvider(
            ProviderConfig(
                provider_id="openai",
                provider_type="openai_compatible",
                api_key="sk-test",
                models=[
                    ModelInfo(
                        provider_id="openai",
                        model_id="chat",
                        display_name="Chat",
                        capabilities=["chat"],
                    )
                ],
            )
        )
    )

    catalog = registry.refresh_catalog()

    assert isinstance(catalog, ModelCatalog)
    assert catalog.get_model("openai/chat").model_id == "chat"
    assert registry.get_provider("openai").provider_id == "openai"


def test_model_router_uses_defaults_and_falls_back_by_capability() -> None:
    """验证模型路由优先使用默认模型，并可按能力回退选择。"""

    registry = ModelRegistry()
    registry.register_provider(
        OpenAICompatibleProvider(
            ProviderConfig(
                provider_id="openai",
                provider_type="openai_compatible",
                api_key="sk-test",
                models=[
                    ModelInfo(
                        provider_id="openai",
                        model_id="chat",
                        display_name="Chat",
                        capabilities=["chat", "summary"],
                    ),
                    ModelInfo(
                        provider_id="openai",
                        model_id="embed",
                        display_name="Embedding",
                        capabilities=["embedding"],
                    ),
                ],
            )
        )
    )
    registry.refresh_catalog()
    router = ModelRouter(
        registry,
        defaults={
            "chat": "openai/chat",
            "summary": "openai/chat",
        },
    )

    chat_selection = router.select_model("chat")
    embedding_selection = router.select_model("embedding")

    assert chat_selection.full_name == "openai/chat"
    assert chat_selection.provider.provider_id == "openai"
    assert embedding_selection.full_name == "openai/embed"


def test_model_router_rejects_invalid_default_model() -> None:
    """验证模型路由会拒绝指向不存在模型的默认配置。"""

    registry = ModelRegistry()
    registry.refresh_catalog()
    router = ModelRouter(registry, defaults={"chat": "openai/missing"})

    with pytest.raises(ModelRoutingError, match="default_model_not_found"):
        router.select_model("chat")


def test_provider_from_config_rejects_unknown_provider_type() -> None:
    """验证 Provider 工厂会拒绝未知的供应商类型。"""

    with pytest.raises(ProviderConfigurationError, match="unsupported_provider_type"):
        provider_from_config(
            ProviderConfig(
                provider_id="custom",
                provider_type="unknown",
            )
        )
