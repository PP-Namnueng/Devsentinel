from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


ReviewDecision = Literal["approve", "request_changes", "needs_discussion"]
IssueSeverity = Literal["critical", "high", "medium", "low"]
IssueCategory = Literal["bug", "security", "performance", "architecture"]


class PRReviewRequest(BaseModel):
    diff: str = Field(min_length=1)
    repository_context: Optional[str] = None
    skill_path: Optional[str] = None


class PRReviewIssue(BaseModel):
    severity: IssueSeverity
    category: IssueCategory
    title: str
    file: Optional[str] = None
    line: Optional[int] = Field(default=None, ge=1)
    evidence: str
    reasoning: str
    suggested_fix: str
    skill_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class PRReviewResult(BaseModel):
    mode: Literal["PR_AUTOPILOT"] = "PR_AUTOPILOT"
    decision: ReviewDecision
    summary: str
    issues: list[PRReviewIssue]
    reviewer_notes: list[str] = Field(default_factory=list)
