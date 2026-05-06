from __future__ import annotations

from typing import Optional


def build_incident_autopsy_prompt(logs: str, skill_memory: str, service_context: Optional[str] = None) -> str:
    context = service_context or "No additional service context was provided."
    return f"""
You are DevSentinel Incident Autopsy.

Analyze pasted production logs. Do not merely summarize.
Reconstruct the causal chain, identify the root cause, and generate actionable prevention steps.
Use engineering memory when relevant and cite specific incident lessons.
Return only valid JSON matching the IncidentAutopsyResult schema.

Engineering memory:
{skill_memory}

Service context:
{context}

Logs:
{logs}
""".strip()
