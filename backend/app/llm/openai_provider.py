import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.answer.context_builder import AnswerContext, AnswerContextItem
from app.llm.provider import (
    ChatModelClient,
    CredentialStatus,
    ModelInfo,
    ModelProvider,
    ProviderConfig,
    ProviderConfigurationError,
    enabled_models,
)


ChatCompletionTransport = Callable[[str, Dict[str, str], Dict[str, Any], float], Dict[str, Any]]


class OpenAICompatibleProvider(ModelProvider):
    """OpenAI-compatible provider adapter，支持自定义 base_url 和配置模型列表。"""

    def __init__(
        self,
        config: ProviderConfig,
        transport: Optional[ChatCompletionTransport] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """保存 provider 配置，并允许测试或上层注入 HTTP transport。"""

        super().__init__(config)
        self._transport = transport or _default_chat_completion_transport
        self._timeout_seconds = timeout_seconds

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

    def get_chat_client(self, model_id: str) -> ChatModelClient:
        """创建可调用 OpenAI-compatible Chat Completions 接口的客户端。"""

        credential_status = self.validate_credentials()
        if not credential_status.ok:
            raise ProviderConfigurationError(credential_status.reason or "invalid_api_key")

        base_client = super().get_chat_client(model_id)
        return OpenAICompatibleChatClient(
            provider_id=base_client.provider_id,
            model_id=base_client.model_id,
            base_url=_normalize_base_url(self.config.base_url),
            api_key=str(self.config.api_key),
            transport=self._transport,
            timeout_seconds=self._timeout_seconds,
        )


@dataclass(frozen=True)
class OpenAICompatibleChatClient(ChatModelClient):
    """Thin client for OpenAI-compatible Chat Completions calls."""

    api_key: str = ""
    transport: Optional[ChatCompletionTransport] = None
    timeout_seconds: float = 30.0

    def generate_answer(self, question, context) -> str:
        """Send the retrieved answer context to a Chat Completions endpoint."""

        payload = {
            "model": self.model_id,
            "messages": _build_messages(str(question), context),
            "temperature": 0.2,
        }
        transport = self.transport or _default_chat_completion_transport
        response = transport(
            f"{_normalize_base_url(self.base_url)}/chat/completions",
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload,
            self.timeout_seconds,
        )
        return _extract_answer_text(response)


def _default_chat_completion_transport(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float,
) -> Dict[str, Any]:
    """Post JSON to a Chat Completions endpoint and return parsed JSON."""

    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise ProviderConfigurationError(f"chat_request_failed: http_{error.code}") from error
    except URLError as error:
        raise ProviderConfigurationError(f"chat_request_failed: {error.reason}") from error

    try:
        parsed = json.loads(raw_body or "{}")
    except json.JSONDecodeError as error:
        raise ProviderConfigurationError("chat_response_invalid_json") from error
    if not isinstance(parsed, dict):
        raise ProviderConfigurationError("chat_response_invalid_shape")
    return parsed


def _build_messages(question: str, context: AnswerContext) -> List[Dict[str, str]]:
    """Build a compact prompt from retrieved chunks and personalization memory."""

    context_blocks = "\n\n".join(
        _format_context_item(index, item)
        for index, item in enumerate(context.items, start=1)
    )
    memory_blocks = "\n".join(
        f"- {memory.get('memory_type', 'memory')}: {memory.get('content', '')}"
        for memory in context.personalization_memories
        if str(memory.get("content", "")).strip()
    )
    user_parts = [
        f"问题：{question.strip()}",
        "可用资料：",
        context_blocks or "无",
    ]
    if memory_blocks:
        user_parts.extend(["个性化记忆：", memory_blocks])

    return [
        {
            "role": "system",
            "content": (
                "你是 Personal Wiki Agent。只能基于用户给定的个人知识库资料回答；"
                "如果资料不足，请明确说明不足，不要编造来源。"
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(user_parts),
        },
    ]


def _format_context_item(index: int, item: AnswerContextItem) -> str:
    """Format one retrieved chunk with stable source metadata."""

    citation = item.citation
    label_parts = [
        f"文档ID={citation.document_id}",
        f"片段ID={citation.chunk_id}",
    ]
    if citation.document_title:
        label_parts.append(f"标题={citation.document_title}")
    if citation.heading_path:
        label_parts.append(f"章节={citation.heading_path}")
    return f"[{index}] {'; '.join(label_parts)}\n{item.text.strip()}"


def _extract_answer_text(response: Dict[str, Any]) -> str:
    """Extract assistant content from a Chat Completions response."""

    try:
        answer = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderConfigurationError("chat_response_missing_content") from error

    answer_text = str(answer or "").strip()
    if not answer_text:
        raise ProviderConfigurationError("empty_model_answer")
    return answer_text


def _normalize_base_url(base_url: Optional[str]) -> str:
    """Normalize custom provider base URL without substituting a hidden default."""

    if not base_url:
        raise ProviderConfigurationError("missing_base_url")
    return base_url.rstrip("/")
