from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from app.schemas.incident import (
    AlertContext,
    DeploymentEvent,
    IncidentEvidencePacket,
    LogEvent,
    MetricSnapshot,
    TraceEvent,
)


class EvidenceRedactor:
    """Remove common secret material before evidence reaches a model."""

    SECRET_PATTERNS = [
        re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization)=([^\s,;]+)"),
        re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+"),
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ]

    def redact_packet(self, packet: IncidentEvidencePacket) -> IncidentEvidencePacket:
        return IncidentEvidencePacket(
            alert=self._redact_model(packet.alert, AlertContext),
            logs=[self._redact_model(item, LogEvent) for item in packet.logs],
            metrics=[self._redact_model(item, MetricSnapshot) for item in packet.metrics],
            deployments=[self._redact_model(item, DeploymentEvent) for item in packet.deployments],
            traces=[self._redact_model(item, TraceEvent) for item in packet.traces],
            raw_context=self._redact_value(packet.raw_context),
            source_provider=packet.source_provider,
            generated_at=packet.generated_at,
            model=packet.model,
            skill_path=packet.skill_path,
        )

    def _redact_model(self, value: BaseModel, model: type[BaseModel]) -> Any:
        return model.model_validate(self._redact_value(value.model_dump(mode="json")))

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_string(value)
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._redact_value(item) for key, item in value.items()}
        return value

    def _redact_string(self, value: str) -> str:
        redacted = value
        for pattern in self.SECRET_PATTERNS:
            redacted = pattern.sub(self._replacement, redacted)
        return redacted

    def _replacement(self, match: re.Match[str]) -> str:
        if len(match.groups()) >= 2:
            return f"{match.group(1)}=[REDACTED]"
        return "[REDACTED]"
