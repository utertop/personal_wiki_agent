from typing import Dict, Iterable, Optional

from app.llm.catalog import ModelCatalog
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.provider import ModelProvider, ProviderConfig, ProviderConfigurationError


class ModelRegistry:
    """统一管理 provider 实例，并负责刷新模型 catalog。"""

    def __init__(self, providers: Optional[Iterable[ModelProvider]] = None) -> None:
        """初始化 provider 注册表；传入 provider 会按 provider_id 建立索引。"""
        self._providers: Dict[str, ModelProvider] = {}
        self.catalog = ModelCatalog()
        for provider in providers or []:
            self.register_provider(provider)

    def register_provider(self, provider: ModelProvider) -> None:
        """注册或替换一个 provider，后续刷新 catalog 时会读取它的模型列表。"""
        self._providers[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> ModelProvider:
        """按 provider_id 获取 provider，不存在时抛出配置异常。"""
        try:
            return self._providers[provider_id]
        except KeyError as error:
            raise ProviderConfigurationError(f"provider_not_found: {provider_id}") from error

    def refresh_catalog(self) -> ModelCatalog:
        """从所有已注册 provider 拉取模型列表，并重建本地 catalog 缓存。"""
        catalog = ModelCatalog()
        for provider in self._providers.values():
            for model in provider.list_models():
                catalog.add_model(model)
        self.catalog = catalog
        return catalog


def provider_from_config(config: ProviderConfig) -> ModelProvider:
    """根据 ProviderConfig 的类型字段构造具体 provider adapter。"""
    if config.provider_type == "openai_compatible":
        return OpenAICompatibleProvider(config)
    if config.provider_type == "ollama":
        return OllamaProvider(config)
    raise ProviderConfigurationError(f"unsupported_provider_type: {config.provider_type}")
