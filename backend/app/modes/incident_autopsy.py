import logging
from time import perf_counter

from pydantic import ValidationError

from app.model_gateway.base import ModelGateway, ModelOutputError
from app.prompts.incident_autopsy import build_incident_autopsy_prompt, build_incident_autopsy_prompt_from_packet
from app.schemas.incident import (
    IncidentAutopsyReport,
    IncidentAutopsyRequest,
    IncidentAutopsyResult,
    IncidentEvidenceCounts,
    IncidentEvidencePacket,
    IncidentRuntimeTrace,
)

logger = logging.getLogger(__name__)


class IncidentAutopsyMode:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def analyze_packet(self, packet: IncidentEvidencePacket, model: str, skill_memory: str) -> IncidentAutopsyReport:
        started_at = perf_counter()
        logger.info(
            "incident_autopsy_started",
            extra={
                "mode": "INCIDENT_AUTOPSY",
                "alert_id": packet.alert.alert_id,
                "service": packet.alert.service,
                "source_provider": packet.source_provider,
                "gateway": self.gateway.__class__.__name__,
                "model": model,
                "logs": len(packet.logs),
                "metrics": len(packet.metrics),
                "deployments": len(packet.deployments),
                "traces": len(packet.traces),
            },
        )

        prompt = build_incident_autopsy_prompt_from_packet(packet, skill_memory)
        logger.info(
            "incident_prompt_generated",
            extra={
                "mode": "INCIDENT_AUTOPSY",
                "prompt_chars": len(prompt),
                "skill_memory_attached": bool(skill_memory.strip()),
                "skill_memory_chars": len(skill_memory),
            },
        )

        raw = self.gateway.generate_json(
            mode="INCIDENT_AUTOPSY",
            model=model,
            prompt=prompt,
            inputs={
                "evidence_packet": packet.model_dump(mode="json"),
                "skill_memory": skill_memory,
            },
        )
        logger.info(
            "incident_schema_validation_started",
            extra={"mode": "INCIDENT_AUTOPSY", "schema": IncidentAutopsyReport.__name__},
        )

        try:
            report = IncidentAutopsyReport.model_validate(raw)
        except ValidationError:
            logger.exception(
                "incident_schema_validation_failed",
                extra={"mode": "INCIDENT_AUTOPSY", "schema": IncidentAutopsyReport.__name__},
            )
            raise

        self._validate_evidence_refs(packet, report)
        logger.info(
            "incident_schema_validation_succeeded",
            extra={"mode": "INCIDENT_AUTOPSY", "schema": IncidentAutopsyReport.__name__},
        )

        provider = getattr(self.gateway, "provider_name", "unknown")
        latency_ms = getattr(self.gateway, "last_generation_latency_ms", None)
        report.runtime = IncidentRuntimeTrace(
            provider=provider,
            runtime_mode="deterministic_demo" if provider == "demo" else "llm",
            gateway=self.gateway.__class__.__name__,
            model=model,
            source_provider=packet.source_provider,
            schema_name=IncidentAutopsyReport.__name__,
            schema_validation_status="passed",
            latency_ms=latency_ms,
            latency_seconds=round(latency_ms / 1000, 3) if latency_ms is not None else None,
            evidence_counts=IncidentEvidenceCounts(
                logs=len(packet.logs),
                metrics=len(packet.metrics),
                deployments=len(packet.deployments),
                traces=len(packet.traces),
            ),
        )

        logger.info(
            "incident_autopsy_completed",
            extra={
                "mode": "INCIDENT_AUTOPSY",
                "alert_id": packet.alert.alert_id,
                "root_cause_candidates": len(report.root_cause_candidates),
                "timeline_events": len(report.timeline),
                "prevention_actions": len(report.prevention_actions),
                "latency_ms": round((perf_counter() - started_at) * 1000),
                "status": "success",
            },
        )
        return report

    def analyze(self, request: IncidentAutopsyRequest, skill_memory: str) -> IncidentAutopsyResult:
        prompt = build_incident_autopsy_prompt(
            logs=request.logs,
            skill_memory=skill_memory,
            service_context=request.service_context,
        )
        raw = self.gateway.generate_json(
            mode="INCIDENT_AUTOPSY",
            model=request.model,
            prompt=prompt,
            inputs={
                "logs": request.logs,
                "service_context": request.service_context,
                "skill_memory": skill_memory,
            },
        )
        return IncidentAutopsyResult.model_validate(raw)

    def _validate_evidence_refs(self, packet: IncidentEvidencePacket, report: IncidentAutopsyReport) -> None:
        valid_refs = {"alert", packet.alert.alert_id}
        valid_refs.update(item.id for item in packet.logs)
        valid_refs.update(item.id for item in packet.metrics)
        valid_refs.update(item.id for item in packet.deployments)
        valid_refs.update(item.id for item in packet.traces)

        refs: list[str] = []
        for symptom in report.detected_symptoms:
            refs.extend(symptom.evidence_refs)
        for event in report.timeline:
            refs.extend(event.evidence_refs)
        for candidate in report.root_cause_candidates:
            refs.extend(candidate.supporting_evidence)
            refs.extend(candidate.contradicting_evidence)
        refs.extend(report.most_likely_root_cause.supporting_evidence)
        refs.extend(report.most_likely_root_cause.contradicting_evidence)
        for action in report.prevention_actions:
            refs.extend(action.related_evidence)

        unknown_refs = sorted({ref for ref in refs if ref not in valid_refs})
        if unknown_refs:
            logger.error(
                "incident_evidence_reference_validation_failed",
                extra={
                    "mode": "INCIDENT_AUTOPSY",
                    "unknown_refs": unknown_refs,
                    "unknown_ref_count": len(unknown_refs),
                },
            )
            raise ModelOutputError(f"Incident report referenced unknown evidence ids: {', '.join(unknown_refs)}")
