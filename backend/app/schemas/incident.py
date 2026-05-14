from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


IncidentSeverity = Literal["sev1", "sev2", "sev3", "sev4"]
ActionPriority = Literal["p0", "p1", "p2"]
GroundingLevel = Literal["grounded", "inferred", "heuristic"]
ValidationStatus = Literal["passed"]


class IncidentAutopsyRequest(BaseModel):
    logs: str = Field(min_length=1)
    service_context: Optional[str] = None
    skill_path: Optional[str] = None
    model: str = "devsentinel-deterministic-demo"


class TimelineEvent(BaseModel):
    timestamp: str
    event: str
    evidence: str


class PreventionAction(BaseModel):
    priority: ActionPriority
    owner: str
    action: str
    rationale: str


class PostMortem(BaseModel):
    impact: str
    root_cause: str
    contributing_factors: list[str]
    what_went_well: list[str]
    what_went_wrong: list[str]
    prevention_plan: list[PreventionAction]


class IncidentAutopsyResult(BaseModel):
    mode: Literal["INCIDENT_AUTOPSY"] = "INCIDENT_AUTOPSY"
    severity: IncidentSeverity
    executive_summary: str
    root_cause: str
    causal_chain: list[str]
    timeline: list[TimelineEvent]
    post_mortem: PostMortem
    skill_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class AlertContext(BaseModel):
    alert_id: str = Field(min_length=1)
    alert_name: str = Field(min_length=1)
    service: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    severity: IncidentSeverity
    started_at: str = Field(min_length=1)
    ended_at: Optional[str] = None
    window_minutes: int = Field(default=30, ge=1, le=1440)
    description: Optional[str] = None
    labels: dict[str, str] = Field(default_factory=dict)
    scenario_id: Optional[str] = None
    evidence_provider: Optional[Literal["fixture", "local_file", "datadog", "loki_prometheus"]] = None
    log_file_path: Optional[str] = None
    model: Optional[str] = None


class LogEvent(BaseModel):
    id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    service: str = Field(min_length=1)
    level: str = Field(min_length=1)
    message: str = Field(min_length=1)
    source: str = Field(min_length=1)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricSnapshot(BaseModel):
    id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    service: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: float
    unit: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeploymentEvent(BaseModel):
    id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    service: str = Field(min_length=1)
    version: Optional[str] = None
    commit_sha: Optional[str] = None
    author: Optional[str] = None
    summary: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    service: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    duration_ms: Optional[float] = None
    status: Optional[str] = None
    trace_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentEvidencePacket(BaseModel):
    alert: AlertContext
    logs: list[LogEvent] = Field(default_factory=list)
    metrics: list[MetricSnapshot] = Field(default_factory=list)
    deployments: list[DeploymentEvent] = Field(default_factory=list)
    traces: list[TraceEvent] = Field(default_factory=list)
    raw_context: Optional[str] = None
    source_provider: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)
    model: Optional[str] = None
    skill_path: Optional[str] = None


class IncidentEvidenceCounts(BaseModel):
    logs: int = 0
    metrics: int = 0
    deployments: int = 0
    traces: int = 0


class IncidentRuntimeTrace(BaseModel):
    provider: str
    runtime_mode: Literal["deterministic_demo", "llm"]
    gateway: str
    model: str
    source_provider: str
    schema_name: str
    schema_validation_status: ValidationStatus
    latency_ms: Optional[int] = None
    latency_seconds: Optional[float] = None
    evidence_counts: IncidentEvidenceCounts


class DetectedSymptom(BaseModel):
    service: str
    summary: str
    grounding: GroundingLevel
    evidence_refs: list[str] = Field(default_factory=list)


class IncidentTimelineEvent(BaseModel):
    timestamp: str
    service: str
    event_type: str
    summary: str
    grounding: GroundingLevel
    evidence_refs: list[str] = Field(default_factory=list)


class RootCauseCandidate(BaseModel):
    title: str
    explanation: str
    grounding: GroundingLevel
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    uncertainty: str


class IncidentPreventionAction(BaseModel):
    priority: ActionPriority
    action: str
    rationale: str
    related_evidence: list[str] = Field(default_factory=list)


class IncidentAutopsyReport(BaseModel):
    mode: Literal["INCIDENT_AUTOPSY"] = "INCIDENT_AUTOPSY"
    incident_title: str
    executive_summary: str
    severity_assessment: str
    affected_services: list[str] = Field(default_factory=list)
    detected_symptoms: list[DetectedSymptom] = Field(default_factory=list)
    timeline: list[IncidentTimelineEvent] = Field(default_factory=list)
    root_cause_candidates: list[RootCauseCandidate] = Field(default_factory=list)
    most_likely_root_cause: RootCauseCandidate
    blast_radius: str
    evidence_summary: str
    contributing_factors: list[str] = Field(default_factory=list)
    prevention_actions: list[IncidentPreventionAction] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    postmortem_markdown: str
    grounding_notes: str
    analysis_limitations: list[str] = Field(default_factory=list)
    runtime: Optional[IncidentRuntimeTrace] = None


class StoredIncident(BaseModel):
    id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    source: str = Field(min_length=1)
    alert_id: str = Field(min_length=1)
    alert_name: str = Field(min_length=1)
    service: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    severity: IncidentSeverity
    status: Literal["completed"] = "completed"
    report: IncidentAutopsyReport
    labels: dict[str, str] = Field(default_factory=dict)
