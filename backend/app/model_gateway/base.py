from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.chat import ChatRequest, ChatResponse, ModelInfo


class ModelGatewayError(RuntimeError):
    pass


class ModelConfigError(ModelGatewayError):
    pass


class ModelOutputError(ModelGatewayError):
    pass


class ModelGateway(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Return a provider-agnostic chat completion."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return demo-friendly model metadata for the active provider."""

    @abstractmethod
    def generate_json(
        self,
        mode: str,
        model: str,
        prompt: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Return parsed JSON for a DevSentinel mode."""
