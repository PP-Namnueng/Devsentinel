from __future__ import annotations

import logging

from app.core.config import Settings, get_settings
from app.model_gateway.base import ModelConfigError, ModelGateway
from app.model_gateway.demo_gateway import DeterministicDemoGateway
from app.schemas.runtime_config import RuntimeProviderConfig
from app.services.runtime_config_service import RuntimeConfigService

logger = logging.getLogger(__name__)


def _runtime_provider_config() -> RuntimeProviderConfig | None:
    try:
        config = RuntimeConfigService().get_model_gateway_config()
    except Exception:
        return None
    if config.provider == "demo":
        return None
    return config


def build_model_gateway(
    settings: Settings | None = None,
    runtime_provider: RuntimeProviderConfig | None = None,
) -> ModelGateway:
    settings = settings or get_settings()
    runtime_provider = runtime_provider or _runtime_provider_config()
    provider = runtime_provider.provider if runtime_provider else settings.model_provider

    if provider == "demo":
        gateway = DeterministicDemoGateway()
        logger.info(
            "provider_selected",
            extra={
                "provider": provider,
                "model": gateway.model_name,
                "runtime_mode": "deterministic_demo",
                "gateway": gateway.__class__.__name__,
            },
        )
        return gateway
    if provider == "openai_compatible":
        from app.model_gateway.openai_gateway import OpenAICompatibleGateway

        base_url = runtime_provider.base_url if runtime_provider and runtime_provider.base_url else settings.openai_base_url
        model = runtime_provider.model if runtime_provider and runtime_provider.model else settings.openai_model
        api_key = runtime_provider.api_key if runtime_provider and runtime_provider.api_key else settings.openai_api_key
        gateway = OpenAICompatibleGateway(
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_seconds=settings.request_timeout_seconds,
        )
        logger.info(
            "provider_selected",
            extra={
                "provider": provider,
                "model": model,
                "runtime_mode": "llm",
                "gateway": gateway.__class__.__name__,
            },
        )
        return gateway
    if provider == "ollama":
        from app.model_gateway.ollama_gateway import OllamaGateway

        base_url = runtime_provider.base_url if runtime_provider and runtime_provider.base_url else settings.ollama_base_url
        model = runtime_provider.model if runtime_provider and runtime_provider.model else settings.ollama_model
        gateway = OllamaGateway(
            base_url=base_url,
            model=model,
            timeout_seconds=settings.request_timeout_seconds,
        )
        logger.info(
            "provider_selected",
            extra={
                "provider": provider,
                "model": model,
                "runtime_mode": "llm",
                "gateway": gateway.__class__.__name__,
            },
        )
        return gateway
    logger.error(
        "provider_selection_failed",
        extra={
            "provider": provider,
            "runtime_mode": "unknown",
        },
    )
    raise ModelConfigError(f"Unsupported MODEL_PROVIDER: {provider}")
