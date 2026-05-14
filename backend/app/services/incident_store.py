from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.incident import AlertContext, IncidentAutopsyReport, StoredIncident

INCIDENT_STORE_PATH = Path(__file__).resolve().parents[2] / "runtime" / "incidents.json"


class IncidentStore:
    def __init__(self, path: Path = INCIDENT_STORE_PATH) -> None:
        self.path = path

    def save(self, alert: AlertContext, report: IncidentAutopsyReport, source: str) -> StoredIncident:
        incident = StoredIncident(
            id=f"incident_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}",
            created_at=datetime.now(timezone.utc).isoformat(),
            source=source,
            alert_id=alert.alert_id,
            alert_name=alert.alert_name,
            service=alert.service,
            environment=alert.environment,
            severity=alert.severity,
            report=report,
            labels=alert.labels,
        )
        incidents = self.list()
        incidents.append(incident)
        self._write(incidents)
        return incident

    def list(self) -> list[StoredIncident]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return [StoredIncident.model_validate(item) for item in data]

    def latest(self) -> StoredIncident | None:
        incidents = self.list()
        if not incidents:
            return None
        return sorted(incidents, key=lambda item: item.created_at, reverse=True)[0]

    def get(self, incident_id: str) -> StoredIncident | None:
        for incident in self.list():
            if incident.id == incident_id:
                return incident
        return None

    def _write(self, incidents: list[StoredIncident]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(incidents, key=lambda item: item.created_at)
        self.path.write_text(
            json.dumps([item.model_dump(mode="json") for item in ordered], indent=2),
            encoding="utf-8",
        )
