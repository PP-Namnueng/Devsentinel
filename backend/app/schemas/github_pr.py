from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.pr_review import PRReviewResult


class GitHubPRReviewRequest(BaseModel):
    owner: str
    repo: str
    pull_number: int = Field(ge=1)
    model: str
    repository_context: Optional[str] = None
    post_comment: bool = True

    @field_validator("owner", "repo", "model")
    @classmethod
    def not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value


class GitHubPRReviewResponse(BaseModel):
    owner: str
    repo: str
    pull_number: int
    model: str
    review: PRReviewResult
    comment_body: str
    posted_to_github: bool
    github_comment_url: Optional[str] = None


class GitHubWebhookReviewResponse(BaseModel):
    status: Literal["accepted", "ignored", "duplicate"]
    reason: Optional[str] = None
    event: Optional[str] = None
    action: Optional[str] = None
    delivery_id: Optional[str] = None
    owner: Optional[str] = None
    repo: Optional[str] = None
    pull_number: Optional[int] = None
    review: Optional[GitHubPRReviewResponse] = None
