from __future__ import annotations

import logging
from datetime import datetime, timezone
from html import escape

import httpx

from app.core.config import Settings, get_settings
from app.schemas.incident import StoredIncident

logger = logging.getLogger(__name__)


class IncidentNotificationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def notify(self, incident: StoredIncident) -> None:
        provider = self.settings.notification_provider
        if provider == "telegram":
            self._notify_telegram(incident)
        elif provider == "slack":
            self._notify_slack(incident)
        elif provider == "webhook":
            self._notify_webhook(incident)

    def _message(self, incident: StoredIncident) -> str:
        message_data = self._message_data(incident)
        latency_line = (
            f"Analysis latency: {message_data['latency']:.1f}s"
            if message_data["latency"] is not None
            else "Analysis latency: n/a"
        )
        return "\n".join(
            [
                "DevSentinel Incident analysis",
                "",
                f"Title: {message_data['title']}",
                f"Alert: {message_data['alert']}",
                f"Service: {message_data['service']}",
                f"Environment: {message_data['environment']}",
                f"Severity: {message_data['severity']}",
                f"Source: {message_data['source']}",
                f"Status: {message_data['status']}",
                f"Detected at: {message_data['detected_at']}",
                f"Analyzed at: {message_data['analyzed_at']}",
                latency_line,
                "",
                f"Most likely root cause ({message_data['root_cause_grounding']}): {message_data['root_cause']}",
                f"Evidence: {message_data['evidence']}",
                f"Top action: {message_data['first_action']}",
                "",
                "Summary:",
                str(message_data["summary"]),
                "",
                f"Open dashboard: {message_data['dashboard_url']}",
            ]
        )

    def _telegram_message(self, incident: StoredIncident) -> str:
        message_data = self._message_data(incident)
        latency = (
            f"{message_data['latency']:.1f}s"
            if message_data["latency"] is not None
            else "n/a"
        )

        def line(label: str, value: object) -> str:
            return f"<b>{escape(label)}:</b> {escape(str(value))}"

        return "\n".join(
            [
                "<b>DevSentinel Incident Analysis</b>",
                "",
                line("Title", message_data["title"]),
                line("Alert", message_data["alert"]),
                line("Service", message_data["service"]),
                line("Environment", message_data["environment"]),
                line("Severity", message_data["severity"]),
                line("Source", message_data["source"]),
                line("Status", message_data["status"]),
                line("Detected at", message_data["detected_at"]),
                line("Analyzed at", message_data["analyzed_at"]),
                line("Analysis latency", latency),
                "",
                line(
                    f"Most likely root cause ({message_data['root_cause_grounding']})",
                    message_data["root_cause"],
                ),
                line("Evidence", message_data["evidence"]),
                line("Top action", message_data["first_action"]),
                "",
                "<b>Summary:</b>",
                escape(str(message_data["summary"])),
                "",
                f'<b>Open dashboard:</b> <a href="{escape(str(message_data["dashboard_url"]), quote=True)}">View incident</a>',
            ]
        )

    def _message_data(self, incident: StoredIncident) -> dict[str, object]:
        root_cause = incident.report.most_likely_root_cause.title
        root_cause_grounding = incident.report.most_likely_root_cause.grounding
        counts = (
            incident.report.runtime.evidence_counts if incident.report.runtime else None
        )
        evidence = (
            f"{counts.logs} logs / {counts.metrics} metrics / {counts.deployments} deployments / {counts.traces} traces"
            if counts
            else "evidence packet available"
        )
        dashboard_url = f"{self.settings.devsentinel_public_url.rstrip('/')}/incidents/{incident.id}"
        summary = incident.report.executive_summary.strip()
        if len(summary) > 520:
            summary = f"{summary[:517].rstrip()}..."
        first_action = (
            incident.report.prevention_actions[0].action
            if incident.report.prevention_actions
            else "Review incident evidence and confirm owner."
        )
        detected_at = self._format_local_timestamp(
            self._first_timeline_timestamp(incident) or incident.created_at
        )
        analyzed_at = self._format_local_timestamp(incident.created_at)
        latency = incident.report.runtime.latency_seconds if incident.report.runtime else None
        return {
            "title": incident.report.incident_title,
            "alert": f"{incident.alert_name} ({incident.alert_id})",
            "service": incident.service,
            "environment": incident.environment,
            "severity": incident.severity,
            "source": incident.source,
            "status": incident.status,
            "detected_at": detected_at,
            "analyzed_at": analyzed_at,
            "latency": latency,
            "root_cause": root_cause,
            "root_cause_grounding": root_cause_grounding,
            "evidence": evidence,
            "first_action": first_action,
            "summary": summary,
            "dashboard_url": dashboard_url,
        }

    def _first_timeline_timestamp(self, incident: StoredIncident) -> str | None:
        if not incident.report.timeline:
            return None
        return sorted(item.timestamp for item in incident.report.timeline)[0]

    def _format_local_timestamp(self, value: str) -> str:
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            local = parsed.astimezone()
            offset = local.strftime("%z")
            offset_label = f"GMT{offset[:3]}:{offset[3:]}" if offset else local.tzname() or "local time"
            return f"{local:%Y-%m-%d %H:%M:%S} {offset_label}"
        except ValueError:
            return value

    def _payload(self, incident: StoredIncident) -> dict[str, object]:
        counts = (
            incident.report.runtime.evidence_counts if incident.report.runtime else None
        )
        dashboard_url = f"{self.settings.devsentinel_public_url.rstrip('/')}/incidents/{incident.id}"
        return {
            "event": "incident_analysis_completed",
            "message": self._message(incident),
            "incident": {
                "id": incident.id,
                "created_at": incident.created_at,
                "source": incident.source,
                "alert_id": incident.alert_id,
                "alert_name": incident.alert_name,
                "service": incident.service,
                "environment": incident.environment,
                "severity": incident.severity,
                "status": incident.status,
                "dashboard_url": dashboard_url,
                "incident_title": incident.report.incident_title,
                "executive_summary": incident.report.executive_summary,
                "root_cause": incident.report.most_likely_root_cause.title,
                "root_cause_grounding": incident.report.most_likely_root_cause.grounding,
                "first_timeline_timestamp": self._first_timeline_timestamp(incident),
                "notification_sent_at": datetime.now(timezone.utc).isoformat(),
                "evidence_counts": counts.model_dump(mode="json") if counts else None,
            },
        }

    def _notify_telegram(self, incident: StoredIncident) -> None:
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            return
        try:
            response = httpx.post(
                f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": self.settings.telegram_chat_id,
                    "text": self._telegram_message(incident),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=8,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(
                "incident_telegram_notification_failed",
                extra={"incident_id": incident.id},
            )

    def _notify_slack(self, incident: StoredIncident) -> None:
        if not self.settings.slack_webhook_url:
            return
        try:
            response = httpx.post(
                self.settings.slack_webhook_url,
                json={"text": self._message(incident)},
                timeout=8,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(
                "incident_slack_notification_failed", extra={"incident_id": incident.id}
            )

    def _notify_webhook(self, incident: StoredIncident) -> None:
        if not self.settings.notification_webhook_url:
            return
        try:
            response = httpx.post(
                self.settings.notification_webhook_url,
                json=self._payload(incident),
                timeout=8,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(
                "incident_webhook_notification_failed",
                extra={"incident_id": incident.id},
            )
