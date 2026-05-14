from __future__ import annotations

import asyncio
import json
import logging
from time import perf_counter
from typing import Any, Optional

import httpx

from app.model_gateway.base import ModelConfigError, ModelGateway, ModelGatewayError, ModelOutputError
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OpenAICompatibleGateway(ModelGateway):
    """OpenAI-compatible provider using /chat/completions."""

    provider_name = "openai_compatible"

    def __init__(self, base_url: str, model: str, api_key: Optional[str], timeout_seconds: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self.api_key:
            raise ModelConfigError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai_compatible")
        selected_model = request.model or self.model
        if not selected_model:
            raise ModelConfigError("No OpenAI-compatible model configured. Set OPENAI_MODEL or pass request.model.")

        payload: dict[str, Any] = {
            "model": selected_model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        started_at = perf_counter()
        endpoint = f"{self.base_url}/chat/completions"
        logger.info(
            "llm_inference_started",
            extra={
                "provider": self.provider_name,
                "model": selected_model,
                "endpoint": endpoint,
                "gateway": self.__class__.__name__,
            },
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    endpoint,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            self.last_inference_latency_ms = round((perf_counter() - started_at) * 1000)
            logger.error(
                "llm_inference_failed",
                extra={
                    "provider": self.provider_name,
                    "model": selected_model,
                    "endpoint": endpoint,
                    "latency_ms": round((perf_counter() - started_at) * 1000),
                    "failure_type": "timeout",
                },
            )
            raise ModelGatewayError("OpenAI-compatible provider timed out") from exc
        except httpx.HTTPStatusError as exc:
            self.last_inference_latency_ms = round((perf_counter() - started_at) * 1000)
            logger.error(
                "llm_inference_failed",
                extra={
                    "provider": self.provider_name,
                    "model": selected_model,
                    "endpoint": endpoint,
                    "latency_ms": round((perf_counter() - started_at) * 1000),
                    "failure_type": "http_status",
                    "status_code": exc.response.status_code,
                },
            )
            raise ModelGatewayError(f"OpenAI-compatible provider returned HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            self.last_inference_latency_ms = round((perf_counter() - started_at) * 1000)
            logger.error(
                "llm_inference_failed",
                extra={
                    "provider": self.provider_name,
                    "model": selected_model,
                    "endpoint": endpoint,
                    "latency_ms": round((perf_counter() - started_at) * 1000),
                    "failure_type": "http_error",
                },
            )
            raise ModelGatewayError(f"OpenAI-compatible provider unavailable: {exc}") from exc

        body = response.json()
        content = self._extract_content(body)
        self.last_inference_latency_ms = round((perf_counter() - started_at) * 1000)
        logger.info(
            "llm_inference_completed",
            extra={
                "provider": self.provider_name,
                "model": selected_model,
                "endpoint": endpoint,
                "latency_ms": self.last_inference_latency_ms,
                "response_chars": len(content),
            },
        )
        return ChatResponse(provider=self.provider_name, model=selected_model, content=content)

    async def list_models(self) -> list[ModelInfo]:
        if not self.api_key:
            raise ModelConfigError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai_compatible")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
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

    def generate_json(
        self,
        mode: str,
        model: str,
        prompt: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "json_generation_started",
            extra={
                "provider": self.provider_name,
                "model": model,
                "mode": mode,
                "gateway": self.__class__.__name__,
                "prompt_chars": len(prompt),
            },
        )
        total_inference_latency_ms = 0
        request = ChatRequest(
            model=model,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Return only valid JSON. Do not wrap it in Markdown. "
                        "Escape newlines and quotes inside string values."
                    ),
                ),
                ChatMessage(role="user", content=prompt),
            ],
            temperature=0,
            max_tokens=4000,
        )
        response = asyncio.run(self.chat(request))
        total_inference_latency_ms += getattr(self, "last_inference_latency_ms", 0)
        try:
            parsed = self._parse_json(response.content)
            self.last_generation_latency_ms = total_inference_latency_ms
            logger.info(
                "json_parse_succeeded",
                extra={
                    "provider": self.provider_name,
                    "model": model,
                    "mode": mode,
                    "repair_attempted": False,
                },
            )
            return parsed
        except ModelOutputError as exc:
            logger.warning(
                "json_parse_failed",
                extra={
                    "provider": self.provider_name,
                    "model": model,
                    "mode": mode,
                    "repair_attempted": False,
                },
            )
            repaired = asyncio.run(self.chat(self._repair_request(model, mode, response.content)))
            total_inference_latency_ms += getattr(self, "last_inference_latency_ms", 0)
            try:
                parsed = self._parse_json(repaired.content)
                self.last_generation_latency_ms = total_inference_latency_ms
                logger.info(
                    "json_parse_succeeded",
                    extra={
                        "provider": self.provider_name,
                        "model": model,
                        "mode": mode,
                        "repair_attempted": True,
                    },
                )
                return parsed
            except ModelOutputError as repair_exc:
                self.last_generation_latency_ms = total_inference_latency_ms
                logger.error(
                    "json_parse_failed",
                    extra={
                        "provider": self.provider_name,
                        "model": model,
                        "mode": mode,
                        "repair_attempted": True,
                    },
                )
                raise ModelOutputError(
                    f"Model returned malformed JSON and repair failed: {repair_exc}"
                ) from exc

    def _repair_request(self, model: str, mode: str, malformed_content: str) -> ChatRequest:
        return ChatRequest(
            model=model,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "You repair malformed JSON. Return exactly one valid JSON object only. "
                        "Do not add markdown, comments, or explanations."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        f"Repair this {mode} JSON so it parses and preserves the same data. "
                        "Use double quotes for all keys and strings, add any missing commas, "
                        "remove trailing commas, and escape code evidence inside strings.\n\n"
                        f"{malformed_content}"
                    ),
                ),
            ],
            temperature=0,
            max_tokens=4000,
        )

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
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ModelOutputError(
                    "Model returned malformed JSON and no JSON object could be extracted"
                ) from exc
            try:
                parsed = json.loads(stripped[start : end + 1])
            except json.JSONDecodeError as nested_exc:
                raise ModelOutputError(f"Model returned malformed JSON: {nested_exc}") from nested_exc
        if not isinstance(parsed, dict):
            raise ModelOutputError("Model JSON output must be an object")
        return parsed
