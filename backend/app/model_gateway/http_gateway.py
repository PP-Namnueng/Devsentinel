from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from app.model_gateway.base import ModelGateway, ModelGatewayError, ModelOutputError


class HttpJsonModelGateway(ModelGateway):
    """OpenAI-compatible JSON gateway for local or hosted coder models."""

    def __init__(self, endpoint: str, model: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.endpoint = endpoint
        self.model = model
        self.api_key = api_key

    def generate_json(self, mode: str, prompt: str, inputs: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": "Return only valid JSON. Do not wrap it in Markdown."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        if self.model:
            payload["model"] = self.model

        try:
            response = httpx.post(self.endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ModelGatewayError(f"Model gateway request failed: {exc}") from exc

        body = response.json()
        content = self._extract_content(body)
        return self._parse_json(content)

    def _extract_content(self, body: dict[str, Any]) -> str:
        if "choices" in body:
            try:
                return body["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise ModelOutputError("Model response did not contain choices[0].message.content") from exc
        if "content" in body and isinstance(body["content"], str):
            return body["content"]
        if isinstance(body, dict):
            return json.dumps(body)
        raise ModelOutputError("Model response shape is unsupported")

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
