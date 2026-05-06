from __future__ import annotations

import asyncio
import json
from typing import Any, Union

import httpx

from app.model_gateway.base import ModelGateway, ModelGatewayError, ModelOutputError
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, ModelInfo


class OllamaGateway(ModelGateway):
    """Ollama provider using /api/chat."""

    provider_name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        options: dict[str, Union[float, int]] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        payload = {
            "model": self.model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
            "options": options,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelGatewayError("Ollama provider timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise ModelGatewayError(f"Ollama provider returned HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ModelGatewayError(f"Ollama provider unavailable: {exc}") from exc

        body = response.json()
        try:
            content = body["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ModelOutputError("Ollama response did not contain message.content") from exc
        return ChatResponse(provider=self.provider_name, model=self.model, content=content)

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelGatewayError("Ollama model listing timed out") from exc
        except httpx.HTTPError:
            return [ModelInfo(id=self.model, provider=self.provider_name)]

        body = response.json()
        return [
            ModelInfo(id=item["name"], provider=self.provider_name)
            for item in body.get("models", [])
            if isinstance(item, dict) and "name" in item
        ] or [ModelInfo(id=self.model, provider=self.provider_name)]

    def generate_json(self, mode: str, prompt: str, inputs: dict[str, Any]) -> dict[str, Any]:
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="Return only valid JSON. Do not wrap it in Markdown."),
                ChatMessage(role="user", content=prompt),
            ],
            temperature=0,
            max_tokens=1600,
        )
        response = asyncio.run(self.chat(request))
        return self._parse_json(response.content)

    def _parse_json(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ModelOutputError(f"Model returned malformed JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ModelOutputError("Model JSON output must be an object")
        return parsed
