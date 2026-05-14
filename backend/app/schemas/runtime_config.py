from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RuntimeRoute(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    label: Optional[str] = None


class IncidentEvidenceConfig(BaseModel):
    provider: Optional[Literal["fixture", "local_file", "datadog", "loki_prometheus"]] = None
    log_file_path: Optional[str] = None
    log_limit: Optional[int] = Field(default=None, ge=1, le=1000)
    loki_base_url: Optional[str] = None
    prometheus_base_url: Optional[str] = None
    datadog_site: Optional[str] = None


class RuntimeProviderConfig(BaseModel):
    provider: Literal["demo", "openai_compatible", "ollama"] = "demo"
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class RuntimeConnectionTestRequest(BaseModel):
    model_gateway: RuntimeProviderConfig


class RuntimeConnectionTestResult(BaseModel):
    provider: str
    ok: bool
    detail: str
    models: list[str] = Field(default_factory=list)


class RuntimeConfig(BaseModel):
    model_gateway: RuntimeProviderConfig = Field(default_factory=RuntimeProviderConfig)
    task_routing: dict[str, RuntimeRoute] = Field(default_factory=dict)
    incident_evidence: IncidentEvidenceConfig = Field(default_factory=IncidentEvidenceConfig)
