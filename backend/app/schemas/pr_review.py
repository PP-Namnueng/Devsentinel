from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ReviewDecision = Literal["approve", "request_changes", "needs_discussion"]
IssueSeverity = Literal["critical", "high", "medium", "low"]
IssueCategory = Literal[
    "security",
    "bug",
    "concurrency",
    "performance",
    "maintainability",
    "architecture",
    "operational_risk",
]
GroundingLevel = Literal["grounded", "inferred", "heuristic", "needs_verification"]


class PRReviewRequest(BaseModel):
    diff: str = Field(min_length=1)
    repository_context: Optional[str] = None
    skill_path: Optional[str] = None
    model: str = "devsentinel-deterministic-demo"


class PRReviewIssue(BaseModel):
    severity: IssueSeverity
    category: IssueCategory
    grounding: GroundingLevel
    title: str
    file: Optional[str] = None
    line: Optional[int] = Field(default=None, ge=1)
    end_line: Optional[int] = Field(default=None, ge=1)
    evidence: str
    reasoning: str
    suggested_fix: str
    skill_references: list[str] = Field(default_factory=list)


class PRReviewGroundingStats(BaseModel):
    grounded: int = 0
    inferred: int = 0
    heuristic: int = 0
    needs_verification: int = 0


class PRReviewRuntime(BaseModel):
    provider: str
    runtime_mode: Literal["deterministic_demo", "llm"]
    gateway: str
    model: str
    schema_name: str
    schema_validation_status: Literal["passed"] = "passed"
    latency_ms: Optional[int] = None
    latency_seconds: Optional[float] = None
    grounding_stats: PRReviewGroundingStats = Field(default_factory=PRReviewGroundingStats)


class PRReviewResult(BaseModel):
    mode: Literal["PR_AUTOPILOT"] = "PR_AUTOPILOT"
    decision: ReviewDecision
    summary: str
    issues: list[PRReviewIssue]
    reviewer_notes: list[str] = Field(default_factory=list)
    runtime: Optional[PRReviewRuntime] = None
