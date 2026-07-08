import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.llm.prompt_builder import build_chat_messages
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
    """OpenAI-compatible provider adapter with configurable base URL and models."""

    def __init__(
        self,
        config: ProviderConfig,
        transport: Optional[ChatCompletionTransport] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        super().__init__(config)
        self._transport = transport or _default_chat_completion_transport
        self._timeout_seconds = timeout_seconds

    @property
    def protocol(self) -> str:
        return "openai_compatible"

    def validate_credentials(self) -> CredentialStatus:
        if not self.config.api_key:
            return CredentialStatus(ok=False, reason="missing_api_key")
        return CredentialStatus(ok=True)

    def list_models(self) -> List[ModelInfo]:
        return enabled_models(self.config.models)

    def get_chat_client(self, model_id: str) -> ChatModelClient:
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
        payload = {
            "model": self.model_id,
            "messages": build_chat_messages(str(question), context),
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
    if not base_url:
        raise ProviderConfigurationError("missing_base_url")
    return base_url.rstrip("/")
