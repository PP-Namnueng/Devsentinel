from __future__ import annotations

from app.core.config import Settings, get_settings
from app.model_gateway.base import ModelConfigError, ModelGateway
from app.model_gateway.demo_gateway import DeterministicDemoGateway


def build_model_gateway(settings: Settings | None = None) -> ModelGateway:
    settings = settings or get_settings()
    if settings.model_provider == "demo":
        return DeterministicDemoGateway()
    if settings.model_provider == "openai_compatible":
        from app.model_gateway.openai_gateway import OpenAICompatibleGateway

        return OpenAICompatibleGateway(
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if settings.model_provider == "ollama":
        from app.model_gateway.ollama_gateway import OllamaGateway

        return OllamaGateway(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    raise ModelConfigError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")
