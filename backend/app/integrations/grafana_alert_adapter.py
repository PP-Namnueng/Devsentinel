from __future__ import annotations

from app.schemas.grafana import GrafanaAlert, GrafanaWebhookPayload
from app.schemas.incident import AlertContext, IncidentSeverity


class GrafanaAlertAdapterError(ValueError):
    pass


class GrafanaAlertAdapter:
    def to_alert_context(self, payload: GrafanaWebhookPayload) -> AlertContext:
        if not payload.alerts:
            raise GrafanaAlertAdapterError("Grafana webhook payload did not include alerts.")

        alert = self._select_alert(payload.alerts)
        labels = {
            **payload.common_labels,
            **alert.labels,
        }
        annotations = {
            **payload.common_annotations,
            **alert.annotations,
        }

        service = self._first(labels, "service", "app", "application", "job")
        if not service:
            raise GrafanaAlertAdapterError("Grafana alert must include a service, app, application, or job label.")

        environment = self._first(labels, "environment", "env", "namespace", default="production")
        alert_name = self._first(labels, "alertname", "rule", default=payload.title or "Grafana alert")
        alert_id = alert.fingerprint or f"grafana-{alert_name}-{service}-{alert.starts_at}"

        return AlertContext(
            alert_id=alert_id,
            alert_name=alert_name,
            service=service,
            environment=environment,
            severity=self._severity(labels),
            started_at=alert.starts_at,
            ended_at=self._ended_at(alert.ends_at),
            window_minutes=self._window_minutes(labels),
            description=self._description(payload, annotations, alert),
            labels={
                **labels,
                "source": "grafana",
                "grafana_status": alert.status or payload.status or "unknown",
            },
            evidence_provider="loki_prometheus",
        )

    def _ended_at(self, value: str | None) -> str | None:
        if not value or value.startswith("0001-01-01"):
            return None
        return value

    def _select_alert(self, alerts: list[GrafanaAlert]) -> GrafanaAlert:
        firing = [alert for alert in alerts if alert.status == "firing"]
        return firing[0] if firing else alerts[0]

    def _first(self, values: dict[str, str], *keys: str, default: str | None = None) -> str | None:
        for key in keys:
            value = values.get(key)
            if value:
                return value
        return default

    def _severity(self, labels: dict[str, str]) -> IncidentSeverity:
        raw = (self._first(labels, "severity", "priority", "level", default="sev2") or "sev2").lower()
        if raw in {"critical", "crit", "p0", "page", "sev1"}:
            return "sev1"
        if raw in {"high", "warning", "warn", "p1", "sev2"}:
            return "sev2"
        if raw in {"medium", "p2", "sev3"}:
            return "sev3"
        return "sev4"

    def _window_minutes(self, labels: dict[str, str]) -> int:
        raw = labels.get("window_minutes") or labels.get("window")
        if not raw:
            return 30
        try:
            return min(max(int(raw), 1), 1440)
        except ValueError:
            return 30

    def _description(
        self,
        payload: GrafanaWebhookPayload,
        annotations: dict[str, str],
        alert: GrafanaAlert,
    ) -> str | None:
        parts = [
            annotations.get("summary"),
            annotations.get("description"),
            payload.message,
            alert.value_string,
            alert.generator_url,
            alert.dashboard_url,
            alert.panel_url,
        ]
        return "\n".join(part for part in parts if part)
