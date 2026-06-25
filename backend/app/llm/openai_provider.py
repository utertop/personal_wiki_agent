from typing import List

from app.llm.provider import CredentialStatus, ModelInfo, ModelProvider, enabled_models


class OpenAICompatibleProvider(ModelProvider):
    """OpenAI-compatible provider adapter，支持自定义 base_url 和配置模型列表。"""

    @property
    def protocol(self) -> str:
        """返回 provider 协议标识，供 registry 和诊断信息使用。"""
        return "openai_compatible"

    def validate_credentials(self) -> CredentialStatus:
        """OpenAI 兼容服务默认需要 API key；缺失时返回结构化失败原因。"""
        if not self.config.api_key:
            return CredentialStatus(ok=False, reason="missing_api_key")
        return CredentialStatus(ok=True)

    def list_models(self) -> List[ModelInfo]:
        """返回配置中的模型列表；MVP 阶段不主动访问远程 /models 接口。"""
        return enabled_models(self.config.models)
