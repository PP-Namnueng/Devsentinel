from __future__ import annotations

from typing import Optional


def build_pr_review_prompt(diff: str, skill_memory: str, repository_context: Optional[str] = None) -> str:
    context = repository_context or "No additional repository context was provided."
    return f"""
You are DevSentinel PR Autopilot.

Review the diff like a senior engineer. Focus only on:
- bugs
- security vulnerabilities
- performance issues
- architecture violations

Use the engineering memory when relevant and cite specific conventions.
Return only valid JSON matching the PRReviewResult schema.

Decision rules:
- request_changes: critical or high-confidence production risk
- needs_discussion: ambiguous design or ownership concern
- approve: no material issues

Engineering memory:
{skill_memory}

Repository context:
{context}

Diff:
{diff}
""".strip()
