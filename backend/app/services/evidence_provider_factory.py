from __future__ import annotations

from app.core.config import Settings, get_settings
from app.schemas.incident import AlertContext
from app.schemas.runtime_config import IncidentEvidenceConfig
from app.services.incident_evidence_provider import (
    DatadogEvidenceProvider,
    FixtureEvidenceProvider,
    IncidentEvidenceProvider,
    LocalFileEvidenceProvider,
    LokiPrometheusEvidenceProvider,
)
from app.services.redaction_service import EvidenceRedactor
from app.services.runtime_config_service import RuntimeConfigService


class RedactingEvidenceProvider(IncidentEvidenceProvider):
    def __init__(self, provider: IncidentEvidenceProvider, redactor: EvidenceRedactor | None = None) -> None:
        self.provider = provider
        self.redactor = redactor or EvidenceRedactor()

    def load_evidence(self, alert: AlertContext):
        return self.redactor.redact_packet(self.provider.load_evidence(alert))


def build_incident_evidence_provider(
    alert: AlertContext,
    settings: Settings | None = None,
    evidence_config: IncidentEvidenceConfig | None = None,
) -> IncidentEvidenceProvider:
    resolved_settings = settings or get_settings()
    resolved_evidence_config = evidence_config or RuntimeConfigService().load().incident_evidence
    provider_name = (
        alert.evidence_provider
        or alert.labels.get("evidence_provider")
        or resolved_evidence_config.provider
        or resolved_settings.incident_evidence_provider
    )
    log_limit = resolved_evidence_config.log_limit or resolved_settings.incident_log_limit

    if provider_name == "local_file":
        provider: IncidentEvidenceProvider = LocalFileEvidenceProvider(
            alert.log_file_path
            or alert.labels.get("log_file_path")
            or resolved_evidence_config.log_file_path
            or resolved_settings.incident_log_file_path,
            log_limit=log_limit,
        )
    elif provider_name == "datadog":
        provider = DatadogEvidenceProvider(
            api_key=resolved_settings.datadog_api_key,
            app_key=resolved_settings.datadog_app_key,
            site=resolved_evidence_config.datadog_site or resolved_settings.datadog_site,
            log_limit=log_limit,
            timeout_seconds=resolved_settings.request_timeout_seconds,
        )
    elif provider_name == "loki_prometheus":
        provider = LokiPrometheusEvidenceProvider(
            loki_base_url=resolved_evidence_config.loki_base_url or resolved_settings.loki_base_url,
            prometheus_base_url=resolved_evidence_config.prometheus_base_url or resolved_settings.prometheus_base_url,
            log_limit=log_limit,
            timeout_seconds=resolved_settings.request_timeout_seconds,
        )
    else:
        provider = FixtureEvidenceProvider()

    return RedactingEvidenceProvider(provider)
