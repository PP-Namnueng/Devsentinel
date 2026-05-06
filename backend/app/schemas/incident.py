from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


IncidentSeverity = Literal["sev1", "sev2", "sev3", "sev4"]
ActionPriority = Literal["p0", "p1", "p2"]


class IncidentAutopsyRequest(BaseModel):
    logs: str = Field(min_length=1)
    service_context: Optional[str] = None
    skill_path: Optional[str] = None


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
