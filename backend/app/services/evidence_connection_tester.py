from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.schemas.runtime_config import IncidentEvidenceConfig
from app.services.runtime_config_service import RuntimeConfigService


class EvidenceDatasourceStatus(BaseModel):
    name: str
    ok: bool
    detail: str


class EvidenceConnectionTestResult(BaseModel):
    provider: str
    ok: bool
    checks: list[EvidenceDatasourceStatus] = Field(default_factory=list)


class EvidenceConnectionTester:
    def __init__(
        self,
        settings: Settings | None = None,
        evidence_config: IncidentEvidenceConfig | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.settings = settings or get_settings()
        self.evidence_config = evidence_config or RuntimeConfigService().load().incident_evidence
        self.timeout_seconds = timeout_seconds

    def test(self) -> EvidenceConnectionTestResult:
        provider = self.evidence_config.provider or self.settings.incident_evidence_provider
        if provider == "fixture":
            checks = [EvidenceDatasourceStatus(name="fixture", ok=True, detail="Fixture evidence provider is available.")]
        elif provider == "local_file":
            checks = [self._test_local_file()]
        elif provider == "datadog":
            checks = [self._test_datadog()]
        elif provider == "loki_prometheus":
            checks = [self._test_loki(), self._test_prometheus()]
        else:
            checks = [EvidenceDatasourceStatus(name=provider, ok=False, detail="Unsupported evidence provider.")]

        return EvidenceConnectionTestResult(
            provider=provider,
            ok=all(check.ok for check in checks),
            checks=checks,
        )

    def _test_local_file(self) -> EvidenceDatasourceStatus:
        path = Path(self.evidence_config.log_file_path or self.settings.incident_log_file_path).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        if not path.exists():
            return EvidenceDatasourceStatus(name="local_file", ok=False, detail=f"Log file not found: {path}")
        if not path.is_file():
            return EvidenceDatasourceStatus(name="local_file", ok=False, detail=f"Log path is not a file: {path}")
        return EvidenceDatasourceStatus(name="local_file", ok=True, detail=f"Readable log file: {path}")

    def _test_datadog(self) -> EvidenceDatasourceStatus:
        if not self.settings.datadog_api_key or not self.settings.datadog_app_key:
            return EvidenceDatasourceStatus(
                name="datadog",
                ok=False,
                detail="DATADOG_API_KEY and DATADOG_APP_KEY must be set in the backend environment.",
            )
        site = self.evidence_config.datadog_site or self.settings.datadog_site
        try:
            response = httpx.get(
                f"https://api.{site}/api/v1/validate",
                headers={"DD-API-KEY": self.settings.datadog_api_key},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            valid = bool(body.get("valid", False))
            return EvidenceDatasourceStatus(
                name="datadog",
                ok=valid,
                detail="Datadog API key validated." if valid else "Datadog API key validation failed.",
            )
        except httpx.HTTPError as exc:
            return EvidenceDatasourceStatus(name="datadog", ok=False, detail=f"Datadog validation failed: {exc}")

    def _test_loki(self) -> EvidenceDatasourceStatus:
        base_url = self.evidence_config.loki_base_url or self.settings.loki_base_url
        if not base_url:
            return EvidenceDatasourceStatus(name="loki", ok=False, detail="LOKI_BASE_URL is not configured.")
        try:
            response = httpx.get(
                f"{base_url.rstrip('/')}/loki/api/v1/labels",
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()
            label_count = len(body.get("data", []))
            return EvidenceDatasourceStatus(name="loki", ok=True, detail=f"Loki reachable; {label_count} labels discovered.")
        except httpx.HTTPError as exc:
            return EvidenceDatasourceStatus(name="loki", ok=False, detail=f"Loki check failed: {exc}")

    def _test_prometheus(self) -> EvidenceDatasourceStatus:
        base_url = self.evidence_config.prometheus_base_url or self.settings.prometheus_base_url
        if not base_url:
            return EvidenceDatasourceStatus(name="prometheus", ok=False, detail="PROMETHEUS_BASE_URL is not configured.")
        try:
            response = httpx.get(
                f"{base_url.rstrip('/')}/api/v1/query",
                params={"query": "up"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()
            result_count = len(body.get("data", {}).get("result", []))
            return EvidenceDatasourceStatus(
                name="prometheus",
                ok=True,
                detail=f"Prometheus reachable; {result_count} up-series returned.",
            )
        except httpx.HTTPError as exc:
            return EvidenceDatasourceStatus(name="prometheus", ok=False, detail=f"Prometheus check failed: {exc}")
