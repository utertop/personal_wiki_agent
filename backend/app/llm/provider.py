from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


class ProviderConfigurationError(ValueError):
    """表示 provider 配置不完整、类型未知或模型能力不匹配。"""


@dataclass(frozen=True)
class CredentialStatus:
    """表示 provider 凭证校验结果，避免在 MVP 阶段直接抛出难懂异常。"""

    ok: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class ModelInfo:
    """描述单个模型的能力和元数据，供 catalog、UI 和 router 统一消费。"""

    provider_id: str
    model_id: str
    display_name: str
    capabilities: List[str]
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    embedding_dimensions: Optional[int] = None
    local: bool = False
    deprecated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """返回 provider_id/model_id 形式的稳定模型标识。"""
        return f"{self.provider_id}/{self.model_id}"

    def supports(self, task: str) -> bool:
        """判断模型是否支持指定任务能力，例如 chat、embedding 或 summary。"""
        return task in self.capabilities


@dataclass(frozen=True)
class ProviderConfig:
    """描述一个模型 provider 的配置形态，敏感 key 可来自环境或凭证存储。"""

    provider_id: str
    provider_type: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    enabled: bool = True
    models: List[ModelInfo] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatModelClient:
    """聊天模型客户端的轻量占位对象，后续真实 HTTP / SDK 调用会挂在这里。"""

    provider_id: str
    model_id: str
    base_url: Optional[str] = None

    def generate_answer(self, question, context) -> str:
        """占位生成接口；真实 provider adapter 应覆盖或替换为可调用客户端。"""
        raise ProviderConfigurationError("chat_generation_not_implemented")


@dataclass(frozen=True)
class EmbeddingModelClient:
    """Embedding 模型客户端的轻量占位对象，后续会桥接真实 embedding 服务。"""

    provider_id: str
    model_id: str
    base_url: Optional[str] = None


class ModelProvider(ABC):
    """所有模型 provider 的抽象基类，上层业务只能依赖该接口。"""

    def __init__(self, config: ProviderConfig) -> None:
        """保存 provider 配置并暴露通用标识字段。"""
        self.config = config
        self.provider_id = config.provider_id

    @property
    @abstractmethod
    def protocol(self) -> str:
        """返回 provider 协议类型，例如 openai_compatible 或 ollama。"""
        raise NotImplementedError

    @abstractmethod
    def validate_credentials(self) -> CredentialStatus:
        """校验 provider 凭证或本地连接配置，返回结构化状态。"""
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """返回当前 provider 可用模型列表，MVP 阶段可直接来自配置。"""
        raise NotImplementedError

    def get_model(self, model_id: str) -> ModelInfo:
        """按 model_id 查找模型，不存在时抛出可读配置异常。"""
        for model in self.list_models():
            if model.model_id == model_id:
                return model
        raise ProviderConfigurationError(f"model_not_found: {self.provider_id}/{model_id}")

    def get_chat_client(self, model_id: str) -> ChatModelClient:
        """创建聊天模型客户端占位对象，并校验模型具备 chat 或 summary 能力。"""
        model = self.get_model(model_id)
        if not (model.supports("chat") or model.supports("summary")):
            raise ProviderConfigurationError(f"model_not_chat_capable: {model.full_name}")
        return ChatModelClient(
            provider_id=self.provider_id,
            model_id=model.model_id,
            base_url=self.config.base_url,
        )

    def get_embedding_client(self, model_id: str) -> EmbeddingModelClient:
        """创建 embedding 模型客户端占位对象，并校验模型具备 embedding 能力。"""
        model = self.get_model(model_id)
        if not model.supports("embedding"):
            raise ProviderConfigurationError(f"model_not_embedding_capable: {model.full_name}")
        return EmbeddingModelClient(
            provider_id=self.provider_id,
            model_id=model.model_id,
            base_url=self.config.base_url,
        )


def enabled_models(models: Sequence[ModelInfo]) -> List[ModelInfo]:
    """过滤掉已废弃模型，作为 provider 默认暴露的可选模型清单。"""
    return [model for model in models if not model.deprecated]
