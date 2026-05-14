from __future__ import annotations

import json
from typing import Optional

from app.schemas.incident import IncidentEvidencePacket


def build_incident_autopsy_prompt_from_packet(packet: IncidentEvidencePacket, skill_memory: str) -> str:
    packet_json = json.dumps(packet.model_dump(mode="json"), indent=2, sort_keys=True)
    evidence_ids = ["alert", packet.alert.alert_id]
    evidence_ids.extend(item.id for item in packet.logs)
    evidence_ids.extend(item.id for item in packet.metrics)
    evidence_ids.extend(item.id for item in packet.deployments)
    evidence_ids.extend(item.id for item in packet.traces)
    evidence_id_json = json.dumps(evidence_ids, indent=2)
    return f"""
You are DevSentinel INCIDENT_AUTOPSY.

Your job is to investigate an incident from an IncidentEvidencePacket and return a structured operational report.
Do not summarize blindly. Reconstruct what happened, separate symptoms from root-cause candidates, explain blast radius, and propose prevention actions tied to observed evidence.

Hard constraints:
- Return only valid JSON matching the IncidentAutopsyReport schema.
- Do not invent services, metrics, log lines, timestamps, deployments, traces, or evidence IDs.
- Evidence references must exactly match one of the allowed evidence IDs listed below.
- Every timeline event, symptom, root-cause candidate, and prevention action must cite evidence_refs from the packet when grounded.
- Use only these grounding values: grounded, inferred, heuristic.
- Do not output numeric confidence scores.
- If the evidence is incomplete, state uncertainty in analysis_limitations or candidate uncertainty.
- Treat model output as candidate analysis, not absolute truth.
- Prevention actions must connect to observed evidence, not generic advice.

IncidentAutopsyReport JSON shape:
{{
  "mode": "INCIDENT_AUTOPSY",
  "incident_title": "short title",
  "executive_summary": "what happened in operational terms",
  "severity_assessment": "realistic severity assessment based on provided evidence",
  "affected_services": ["service names from evidence"],
  "detected_symptoms": [
    {{"service": "service", "summary": "symptom", "grounding": "grounded", "evidence_refs": ["log-1"]}}
  ],
  "timeline": [
    {{"timestamp": "ISO or source timestamp", "service": "service", "event_type": "alert|log|metric|deployment|trace|analysis", "summary": "event", "grounding": "grounded", "evidence_refs": ["metric-1"]}}
  ],
  "root_cause_candidates": [
    {{"title": "candidate", "explanation": "why it may explain the incident", "grounding": "grounded", "supporting_evidence": ["deploy-1"], "contradicting_evidence": [], "uncertainty": "what is not proven"}}
  ],
  "most_likely_root_cause": {{"title": "candidate", "explanation": "why this is most likely", "grounding": "grounded", "supporting_evidence": ["deploy-1"], "contradicting_evidence": [], "uncertainty": "remaining uncertainty"}},
  "blast_radius": "services, users, operations realistically affected by evidence",
  "evidence_summary": "brief inventory of logs, metrics, deployments, traces used",
  "contributing_factors": ["specific factors supported by evidence"],
  "prevention_actions": [
    {{"priority": "p1", "action": "specific action", "rationale": "why this prevents recurrence", "related_evidence": ["metric-1"]}}
  ],
  "follow_up_questions": ["questions that would reduce uncertainty"],
  "postmortem_markdown": "postmortem-ready markdown",
  "grounding_notes": "how grounded/inferred/heuristic claims were handled",
  "analysis_limitations": ["known evidence gaps"]
}}

Allowed evidence IDs:
{evidence_id_json}

Engineering governance memory:
{skill_memory}

IncidentEvidencePacket:
{packet_json}
""".strip()


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
