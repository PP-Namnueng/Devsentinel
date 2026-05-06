from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import httpx

from app.model_gateway.base import ModelConfigError, ModelGateway, ModelGatewayError, ModelOutputError
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, ModelInfo


class OpenAICompatibleGateway(ModelGateway):
    """OpenAI-compatible provider using /chat/completions."""

    provider_name = "openai"

    def __init__(self, base_url: str, model: str, api_key: Optional[str]) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self.api_key:
            raise ModelConfigError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelGatewayError("OpenAI-compatible provider timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise ModelGatewayError(f"OpenAI-compatible provider returned HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ModelGatewayError(f"OpenAI-compatible provider unavailable: {exc}") from exc

        body = response.json()
        content = self._extract_content(body)
        return ChatResponse(provider=self.provider_name, model=self.model, content=content)

    async def list_models(self) -> list[ModelInfo]:
        if not self.api_key:
            raise ModelConfigError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai")
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(f"{self.base_url}/models", headers=self._headers())
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelGatewayError("OpenAI-compatible model listing timed out") from exc
        except httpx.HTTPError:
            return [ModelInfo(id=self.model, provider=self.provider_name)]

        body = response.json()
        return [
            ModelInfo(id=item["id"], provider=self.provider_name)
            for item in body.get("data", [])
            if isinstance(item, dict) and "id" in item
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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_content(self, body: dict[str, Any]) -> str:
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelOutputError("Provider response did not contain choices[0].message.content") from exc

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
