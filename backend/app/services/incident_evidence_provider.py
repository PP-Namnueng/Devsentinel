from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypeVar

import httpx

from pydantic import BaseModel

from app.schemas.incident import (
    AlertContext,
    DeploymentEvent,
    IncidentEvidencePacket,
    LogEvent,
    MetricSnapshot,
    TraceEvent,
)


class IncidentEvidenceError(RuntimeError):
    pass


class IncidentEvidenceProvider(ABC):
    @abstractmethod
    def load_evidence(self, alert: AlertContext) -> IncidentEvidencePacket:
        """Normalize source evidence into an IncidentEvidencePacket."""


T = TypeVar("T", bound=BaseModel)


class FixtureEvidenceProvider(IncidentEvidenceProvider):
    def __init__(self, fixture_root: Path | None = None) -> None:
        self.fixture_root = fixture_root or Path(__file__).resolve().parents[1] / "incident_fixtures"

    def load_evidence(self, alert: AlertContext) -> IncidentEvidencePacket:
        scenario_id = alert.scenario_id or alert.labels.get("scenario_id")
        if not scenario_id:
            raise IncidentEvidenceError("Alert must include scenario_id for fixture evidence loading.")

        scenario_path = self.fixture_root / scenario_id
        if not scenario_path.is_dir():
            raise IncidentEvidenceError(f"Incident fixture not found: {scenario_id}")

        fixture_alert = self._load_model(scenario_path / "alert.json", AlertContext)
        resolved_alert = fixture_alert.model_copy(
            update={
                "alert_id": alert.alert_id or fixture_alert.alert_id,
                "model": alert.model or fixture_alert.model,
                "scenario_id": scenario_id,
                "labels": {
                    **fixture_alert.labels,
                    **alert.labels,
                    "scenario_id": scenario_id,
                },
            }
        )

        return IncidentEvidencePacket(
            alert=resolved_alert,
            logs=self._load_model_list(scenario_path / "logs.json", LogEvent),
            metrics=self._load_model_list(scenario_path / "metrics.json", MetricSnapshot),
            deployments=self._load_model_list(scenario_path / "deployments.json", DeploymentEvent),
            traces=self._load_model_list(scenario_path / "traces.json", TraceEvent),
            raw_context=self._load_optional_text(scenario_path / "context.txt"),
            source_provider="fixture",
            generated_at=datetime.now(timezone.utc).isoformat(),
            model=alert.model,
        )

    def _load_json(self, path: Path) -> object:
        if not path.exists():
            raise IncidentEvidenceError(f"Missing incident fixture file: {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_model(self, path: Path, model: type[T]) -> T:
        return model.model_validate(self._load_json(path))

    def _load_model_list(self, path: Path, model: type[T]) -> list[T]:
        if not path.exists():
            return []
        data = self._load_json(path)
        if not isinstance(data, list):
            raise IncidentEvidenceError(f"Incident fixture file must contain a JSON array: {path.name}")
        return [model.model_validate(item) for item in data]

    def _load_optional_text(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8").strip() or None


class LocalFileEvidenceProvider(IncidentEvidenceProvider):
    def __init__(self, log_file_path: str | Path, log_limit: int = 200) -> None:
        self.log_file_path = Path(log_file_path).expanduser()
        self.log_limit = log_limit
        if not self.log_file_path.is_absolute():
            self.log_file_path = Path(__file__).resolve().parents[2] / self.log_file_path

    def load_evidence(self, alert: AlertContext) -> IncidentEvidencePacket:
        if not self.log_file_path.exists():
            raise IncidentEvidenceError(f"Incident log file not found: {self.log_file_path}")
        if not self.log_file_path.is_file():
            raise IncidentEvidenceError(f"Incident log path is not a file: {self.log_file_path}")

        lines = [
            line.strip()
            for line in self.log_file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]
        logs = [self._parse_log_line(index, line, alert.service) for index, line in enumerate(lines[-self.log_limit :], start=1)]
        return IncidentEvidencePacket(
            alert=alert,
            logs=logs,
            metrics=[],
            deployments=[],
            traces=[],
            raw_context=f"local_file={self.log_file_path}",
            source_provider="local_file",
            generated_at=datetime.now(timezone.utc).isoformat(),
            model=alert.model,
        )

    def _parse_log_line(self, index: int, line: str, default_service: str) -> LogEvent:
        match = re.match(
            r"^(?P<timestamp>\S+)\s+(?P<level>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL)\s+(?P<service>[\w.-]+)?\s*(?P<message>.*)$",
            line,
            flags=re.IGNORECASE,
        )
        if match:
            level = match.group("level").upper()
            service = match.group("service") or default_service
            message = match.group("message") or line
            timestamp = match.group("timestamp")
        else:
            level = self._infer_level(line)
            service = default_service
            message = line
            timestamp = datetime.now(timezone.utc).isoformat()

        return LogEvent(
            id=f"log-file-{index}",
            timestamp=timestamp,
            service=service,
            level=level,
            message=message,
            source="local_file",
            trace_id=self._extract_key_value(message, "trace_id"),
            metadata={
                "line_number": index,
                "raw": line,
                "request_id": self._extract_key_value(message, "request_id"),
                "status": self._extract_key_value(message, "status"),
                "duration_ms": self._extract_key_value(message, "duration_ms"),
            },
        )

    def _infer_level(self, line: str) -> str:
        lower = line.lower()
        if "error" in lower or "exception" in lower or "timeout" in lower:
            return "ERROR"
        if "warn" in lower or "degraded" in lower:
            return "WARN"
        return "INFO"

    def _extract_key_value(self, line: str, key: str) -> str | None:
        match = re.search(rf"\b{re.escape(key)}=([^\s,]+)", line)
        if not match:
            return None
        return match.group(1).strip('"')


class DatadogEvidenceProvider(IncidentEvidenceProvider):
    def __init__(
        self,
        api_key: str | None,
        app_key: str | None,
        site: str,
        log_limit: int = 200,
        timeout_seconds: float = 20.0,
    ) -> None:
        if not api_key or not app_key:
            raise IncidentEvidenceError("DATADOG_API_KEY and DATADOG_APP_KEY are required for datadog evidence.")
        self.api_key = api_key
        self.app_key = app_key
        self.site = site
        self.log_limit = log_limit
        self.timeout_seconds = timeout_seconds
        self.base_url = f"https://api.{site}".rstrip("/")

    def load_evidence(self, alert: AlertContext) -> IncidentEvidencePacket:
        start, end = self._window(alert)
        headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            logs = self._load_logs(client, headers, alert, start, end)
            metrics = self._load_metric_snapshots(client, headers, alert, start, end)

        return IncidentEvidencePacket(
            alert=alert,
            logs=logs,
            metrics=metrics,
            deployments=[],
            traces=[],
            raw_context=f"datadog_site={self.site}; window={start.isoformat()}..{end.isoformat()}",
            source_provider="datadog",
            generated_at=datetime.now(timezone.utc).isoformat(),
            model=alert.model,
        )

    def _load_logs(
        self,
        client: httpx.Client,
        headers: dict[str, str],
        alert: AlertContext,
        start: datetime,
        end: datetime,
    ) -> list[LogEvent]:
        payload = {
            "filter": {
                "query": f"service:{alert.service} env:{alert.environment}",
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
            "sort": "timestamp",
            "page": {"limit": self.log_limit},
        }
        response = client.post(f"{self.base_url}/api/v2/logs/events/search", headers=headers, json=payload)
        self._raise_provider_error(response, "Datadog logs query failed")
        body = response.json()
        events: list[LogEvent] = []
        for index, item in enumerate(body.get("data", []), start=1):
            attributes = item.get("attributes", {})
            event_id = str(item.get("id") or f"datadog-log-{index}")
            message = str(attributes.get("message") or attributes.get("attributes", {}).get("message") or "Datadog log event")
            events.append(
                LogEvent(
                    id=event_id,
                    timestamp=str(attributes.get("timestamp") or start.isoformat()),
                    service=str(attributes.get("service") or alert.service),
                    level=str(attributes.get("status") or "INFO").upper(),
                    message=message,
                    source="datadog",
                    trace_id=self._nested_string(attributes, ["attributes", "trace_id"]),
                    metadata={
                        "host": attributes.get("host"),
                        "tags": attributes.get("tags", []),
                        "raw_id": item.get("id"),
                    },
                )
            )
        return events

    def _load_metric_snapshots(
        self,
        client: httpx.Client,
        headers: dict[str, str],
        alert: AlertContext,
        start: datetime,
        end: datetime,
    ) -> list[MetricSnapshot]:
        metric_queries = [
            ("error_rate", f"avg:trace.http.request.errors{{service:{alert.service},env:{alert.environment}}}"),
            ("latency_p95", f"p95:trace.http.request.duration{{service:{alert.service},env:{alert.environment}}}"),
        ]
        snapshots: list[MetricSnapshot] = []
        for metric_name, query in metric_queries:
            response = client.get(
                f"{self.base_url}/api/v1/query",
                headers=headers,
                params={"from": int(start.timestamp()), "to": int(end.timestamp()), "query": query},
            )
            if response.status_code == 400:
                continue
            self._raise_provider_error(response, f"Datadog metric query failed: {metric_name}")
            body = response.json()
            series = body.get("series", [])
            point = self._last_point(series)
            if point is None:
                continue
            snapshots.append(
                MetricSnapshot(
                    id=f"datadog-metric-{metric_name}",
                    timestamp=end.isoformat(),
                    service=alert.service,
                    metric_name=metric_name,
                    value=float(point),
                    metadata={"query": query, "series_count": len(series)},
                )
            )
        return snapshots

    def _window(self, alert: AlertContext) -> tuple[datetime, datetime]:
        started_at = _parse_datetime(alert.started_at)
        ended_at = _parse_datetime(alert.ended_at) if alert.ended_at else started_at + timedelta(minutes=alert.window_minutes)
        if ended_at <= started_at:
            ended_at = min(datetime.now(timezone.utc), started_at + timedelta(minutes=alert.window_minutes))
        return started_at - timedelta(minutes=alert.window_minutes), ended_at

    def _last_point(self, series: list[dict[str, Any]]) -> float | None:
        for item in series:
            points = item.get("pointlist") or []
            for point in reversed(points):
                if isinstance(point, list) and len(point) >= 2 and point[1] is not None:
                    return float(point[1])
        return None

    def _nested_string(self, value: dict[str, Any], path: list[str]) -> str | None:
        current: Any = value
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return str(current) if current is not None else None

    def _raise_provider_error(self, response: httpx.Response, message: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise IncidentEvidenceError(f"{message}: HTTP {response.status_code}") from exc


class LokiPrometheusEvidenceProvider(IncidentEvidenceProvider):
    def __init__(
        self,
        loki_base_url: str | None,
        prometheus_base_url: str | None,
        log_limit: int = 200,
        timeout_seconds: float = 20.0,
    ) -> None:
        if not loki_base_url and not prometheus_base_url:
            raise IncidentEvidenceError("LOKI_BASE_URL or PROMETHEUS_BASE_URL is required for loki_prometheus evidence.")
        self.loki_base_url = loki_base_url.rstrip("/") if loki_base_url else None
        self.prometheus_base_url = prometheus_base_url.rstrip("/") if prometheus_base_url else None
        self.log_limit = log_limit
        self.timeout_seconds = timeout_seconds

    def load_evidence(self, alert: AlertContext) -> IncidentEvidencePacket:
        start, end = self._window(alert)
        metric_time = min(end, datetime.now(timezone.utc))
        with httpx.Client(timeout=self.timeout_seconds) as client:
            logs = self._load_loki_logs(client, alert, start, end) if self.loki_base_url else []
            metrics = self._load_prometheus_metrics(client, alert, metric_time) if self.prometheus_base_url else []

        return IncidentEvidencePacket(
            alert=alert,
            logs=logs,
            metrics=metrics,
            deployments=[],
            traces=[],
            raw_context=f"loki={bool(self.loki_base_url)}; prometheus={bool(self.prometheus_base_url)}; window={start.isoformat()}..{end.isoformat()}",
            source_provider="loki_prometheus",
            generated_at=datetime.now(timezone.utc).isoformat(),
            model=alert.model,
        )

    def _load_loki_logs(self, client: httpx.Client, alert: AlertContext, start: datetime, end: datetime) -> list[LogEvent]:
        query = f'{{service="{alert.service}", environment="{alert.environment}"}}'
        response = client.get(
            f"{self.loki_base_url}/loki/api/v1/query_range",
            params={
                "query": query,
                "start": int(start.timestamp() * 1_000_000_000),
                "end": int(end.timestamp() * 1_000_000_000),
                "limit": self.log_limit,
                "direction": "forward",
            },
        )
        self._raise_provider_error(response, "Loki logs query failed")
        body = response.json()
        logs: list[LogEvent] = []
        index = 1
        for stream in body.get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            for timestamp_ns, message in stream.get("values", []):
                logs.append(
                    LogEvent(
                        id=f"loki-log-{index}",
                        timestamp=_timestamp_ns_to_iso(timestamp_ns),
                        service=str(labels.get("service") or alert.service),
                        level=_infer_level(message),
                        message=str(message),
                        source="loki",
                        metadata={"labels": labels},
                    )
                )
                index += 1
        return logs

    def _load_prometheus_metrics(self, client: httpx.Client, alert: AlertContext, end: datetime) -> list[MetricSnapshot]:
        queries = [
            ("http_error_rate", f'sum(rate(http_requests_total{{service="{alert.service}",status=~"5.."}}[5m]))'),
            ("request_latency_p95", f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{alert.service}"}}[5m])) by (le))'),
        ]
        snapshots: list[MetricSnapshot] = []
        for metric_name, query in queries:
            response = client.get(f"{self.prometheus_base_url}/api/v1/query", params={"query": query, "time": end.timestamp()})
            self._raise_provider_error(response, f"Prometheus metric query failed: {metric_name}")
            body = response.json()
            result = body.get("data", {}).get("result", [])
            if not result:
                continue
            raw_value = result[0].get("value", [None, None])[1]
            if raw_value is None:
                continue
            snapshots.append(
                MetricSnapshot(
                    id=f"prometheus-metric-{metric_name}",
                    timestamp=end.isoformat(),
                    service=alert.service,
                    metric_name=metric_name,
                    value=float(raw_value),
                    metadata={"query": query, "result_count": len(result)},
                )
            )
        return snapshots

    def _window(self, alert: AlertContext) -> tuple[datetime, datetime]:
        started_at = _parse_datetime(alert.started_at)
        ended_at = _parse_datetime(alert.ended_at) if alert.ended_at else started_at + timedelta(minutes=alert.window_minutes)
        if ended_at <= started_at:
            ended_at = min(datetime.now(timezone.utc), started_at + timedelta(minutes=alert.window_minutes))
        return started_at - timedelta(minutes=alert.window_minutes), ended_at

    def _raise_provider_error(self, response: httpx.Response, message: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise IncidentEvidenceError(f"{message}: HTTP {response.status_code}") from exc


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_ns_to_iso(value: str) -> str:
    return datetime.fromtimestamp(int(value) / 1_000_000_000, tz=timezone.utc).isoformat()


def _infer_level(message: str) -> str:
    lower = message.lower()
    if "error" in lower or "exception" in lower or "timeout" in lower:
        return "ERROR"
    if "warn" in lower or "degraded" in lower:
        return "WARN"
    return "INFO"
