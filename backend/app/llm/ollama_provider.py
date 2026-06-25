from typing import List

from app.llm.provider import CredentialStatus, ModelInfo, ModelProvider, enabled_models


class OllamaProvider(ModelProvider):
    """Ollama 本地 provider adapter，不需要 API key，默认面向本机模型服务。"""

    @property
    def protocol(self) -> str:
        """返回 provider 协议标识，供 registry 和路由层识别本地 provider。"""
        return "ollama"

    def validate_credentials(self) -> CredentialStatus:
        """Ollama MVP 阶段只校验配置形态，不主动探测本地服务是否在线。"""
        return CredentialStatus(ok=True)

    def list_models(self) -> List[ModelInfo]:
        """返回配置中的本地模型列表；后续可接入 Ollama tags 接口做自动发现。"""
        return enabled_models(self.config.models)
