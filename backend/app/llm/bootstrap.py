from typing import Mapping, Optional

from app.core.settings import AppSettings, ModelInfoConfig, ProviderSettings
from app.llm.provider import ModelInfo, ProviderConfig
from app.llm.registry import ModelRegistry, provider_from_config
from app.llm.router import ModelRouter


def build_model_router(
    settings: AppSettings,
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[ModelRouter]:
    """Build a ModelRouter from configured providers, or return None when absent."""

    if not settings.model.providers:
        return None

    env = environ or {}
    registry = ModelRegistry()
    for provider_id, provider_settings in settings.model.providers.items():
        if not provider_settings.enabled:
            continue
        registry.register_provider(
            provider_from_config(
                _provider_config(provider_id, provider_settings, env)
            )
        )

    if not registry.refresh_catalog().list_models():
        return None
    return ModelRouter(registry, defaults=settings.model.defaults)


def _provider_config(
    provider_id: str,
    settings: ProviderSettings,
    environ: Mapping[str, str],
) -> ProviderConfig:
    """Convert settings into the runtime provider config consumed by adapters."""

    return ProviderConfig(
        provider_id=provider_id,
        provider_type=settings.type,
        base_url=settings.base_url,
        api_key=_resolve_api_key(settings, environ),
        enabled=settings.enabled,
        models=[
            _model_info(provider_id, model)
            for model in settings.models
        ],
        metadata=dict(settings.metadata),
    )


def _resolve_api_key(settings: ProviderSettings, environ: Mapping[str, str]) -> Optional[str]:
    """Resolve provider API key from the configured environment variable."""

    if not settings.api_key_env:
        return None
    value = environ.get(settings.api_key_env)
    return value.strip() if value else None


def _model_info(provider_id: str, model: ModelInfoConfig) -> ModelInfo:
    """Convert configured model metadata into runtime ModelInfo."""

    return ModelInfo(
        provider_id=provider_id,
        model_id=model.id,
        display_name=model.display_name,
        capabilities=list(model.capabilities),
        context_window=model.context_window,
        max_output_tokens=model.max_output_tokens,
        embedding_dimensions=model.embedding_dimensions,
        local=model.local,
        deprecated=model.deprecated,
        metadata=dict(model.metadata),
    )
