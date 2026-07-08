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


OllamaChatTransport = Callable[[str, Dict[str, Any], float], Dict[str, Any]]


class OllamaProvider(ModelProvider):
    """Ollama local provider adapter."""

    def __init__(
        self,
        config: ProviderConfig,
        transport: Optional[OllamaChatTransport] = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        super().__init__(config)
        self._transport = transport or _default_ollama_chat_transport
        self._timeout_seconds = timeout_seconds

    @property
    def protocol(self) -> str:
        return "ollama"

    def validate_credentials(self) -> CredentialStatus:
        return CredentialStatus(ok=True)

    def list_models(self) -> List[ModelInfo]:
        return enabled_models(self.config.models)

    def get_chat_client(self, model_id: str) -> ChatModelClient:
        base_client = super().get_chat_client(model_id)
        return OllamaChatClient(
            provider_id=base_client.provider_id,
            model_id=base_client.model_id,
            base_url=_normalize_base_url(self.config.base_url),
            transport=self._transport,
            timeout_seconds=self._timeout_seconds,
        )


@dataclass(frozen=True)
class OllamaChatClient(ChatModelClient):
    """Thin client for Ollama chat calls."""

    transport: Optional[OllamaChatTransport] = None
    timeout_seconds: float = 60.0

    def generate_answer(self, question, context) -> str:
        payload = {
            "model": self.model_id,
            "messages": build_chat_messages(str(question), context),
            "stream": False,
        }
        transport = self.transport or _default_ollama_chat_transport
        response = transport(
            f"{_normalize_base_url(self.base_url)}/api/chat",
            payload,
            self.timeout_seconds,
        )
        return _extract_answer_text(response)


def _default_ollama_chat_transport(
    url: str,
    payload: Dict[str, Any],
    timeout: float,
) -> Dict[str, Any]:
    """Post JSON to Ollama `/api/chat` and return parsed JSON."""

    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise ProviderConfigurationError(f"ollama_request_failed: http_{error.code}") from error
    except URLError as error:
        raise ProviderConfigurationError(f"ollama_request_failed: {error.reason}") from error

    try:
        parsed = json.loads(raw_body or "{}")
    except json.JSONDecodeError as error:
        raise ProviderConfigurationError("ollama_response_invalid_json") from error
    if not isinstance(parsed, dict):
        raise ProviderConfigurationError("ollama_response_invalid_shape")
    return parsed


def _extract_answer_text(response: Dict[str, Any]) -> str:
    """Extract assistant content from an Ollama chat response."""

    try:
        answer = response["message"]["content"]
    except (KeyError, TypeError) as error:
        raise ProviderConfigurationError("ollama_response_missing_content") from error

    answer_text = str(answer or "").strip()
    if not answer_text:
        raise ProviderConfigurationError("empty_model_answer")
    return answer_text


def _normalize_base_url(base_url: Optional[str]) -> str:
    if not base_url:
        return "http://localhost:11434"
    return base_url.rstrip("/")
