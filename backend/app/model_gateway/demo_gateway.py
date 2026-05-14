import logging
from time import perf_counter
from typing import Any

from app.model_gateway.base import ModelGateway
from app.schemas.chat import ChatRequest, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class DeterministicDemoGateway(ModelGateway):
    """Stable fallback for hackathon demos and offline development."""

    provider_name = "demo"
    model_name = "devsentinel-deterministic-demo"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        last_user_message = next((message.content for message in reversed(request.messages) if message.role == "user"), "")
        selected_model = request.model or self.model_name
        content = (
            "DevSentinel demo runtime is healthy: deterministic provider, SKILL.md governance loaded, "
            "and provider switching is controlled by MODEL_PROVIDER."
        )
        if last_user_message:
            content = f"{content} Last user request received: {last_user_message[:180]}"
        return ChatResponse(provider=self.provider_name, model=selected_model, content=content)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id=self.model_name, provider=self.provider_name)]

    def generate_json(
        self,
        mode: str,
        model: str,
        prompt: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        started_at = perf_counter()
        logger.info(
            "deterministic_gateway_invoked",
            extra={
                "provider": self.provider_name,
                "model": model or self.model_name,
                "mode": mode,
                "runtime_mode": "deterministic_demo",
                "gateway": self.__class__.__name__,
                "prompt_chars": len(prompt),
            },
        )
        if mode == "PR_AUTOPILOT":
            result = self._review_pr(inputs.get("diff", ""))
            self.last_generation_latency_ms = round((perf_counter() - started_at) * 1000)
            return result
        if mode == "INCIDENT_AUTOPSY":
            if "evidence_packet" in inputs:
                result = self._autopsy_incident_packet(inputs.get("evidence_packet", {}))
            else:
                result = self._autopsy_incident(inputs.get("logs", ""))
            self.last_generation_latency_ms = round((perf_counter() - started_at) * 1000)
            return result
        raise ValueError(f"Unsupported mode: {mode}")

    def _autopsy_incident_packet(self, packet: dict[str, Any]) -> dict[str, Any]:
        alert = packet.get("alert", {})
        logs = packet.get("logs", [])
        metrics = packet.get("metrics", [])
        deployments = packet.get("deployments", [])
        traces = packet.get("traces", [])
        service = alert.get("service", "unknown-service")
        alert_id = alert.get("alert_id", "alert")
        evidence_refs = [alert_id]
        evidence_refs.extend(item.get("id") for item in logs[:2] if item.get("id"))
        evidence_refs.extend(item.get("id") for item in metrics[:2] if item.get("id"))
        deployment_refs = [item.get("id") for item in deployments if item.get("id")]
        candidate_refs = deployment_refs[:1] or evidence_refs[:2]
        first_timestamp = alert.get("started_at", "")
        return {
            "mode": "INCIDENT_AUTOPSY",
            "incident_title": f"{service} incident investigation",
            "executive_summary": (
                f"Deterministic demo analysis inspected {len(logs)} logs, {len(metrics)} metrics, "
                f"{len(deployments)} deployments, and {len(traces)} traces for {service}."
            ),
            "severity_assessment": f"{alert.get('severity', 'sev3')} based on the incoming alert and attached evidence.",
            "affected_services": sorted({service, *(item.get("service", service) for item in logs + metrics + deployments + traces)}),
            "detected_symptoms": [
                {
                    "service": service,
                    "summary": alert.get("description") or alert.get("alert_name") or "Incident symptoms reported by alert.",
                    "grounding": "grounded",
                    "evidence_refs": evidence_refs[:3],
                }
            ],
            "timeline": [
                {
                    "timestamp": first_timestamp,
                    "service": service,
                    "event_type": "alert",
                    "summary": alert.get("alert_name", "Incident alert fired"),
                    "grounding": "grounded",
                    "evidence_refs": [alert_id],
                }
            ]
            + [
                {
                    "timestamp": item.get("timestamp", first_timestamp),
                    "service": item.get("service", service),
                    "event_type": "log",
                    "summary": item.get("message", "Log event"),
                    "grounding": "grounded",
                    "evidence_refs": [item.get("id")],
                }
                for item in logs[:3]
                if item.get("id")
            ],
            "root_cause_candidates": [
                {
                    "title": "Recent runtime change or dependency pressure is correlated with the incident window",
                    "explanation": (
                        "The demo provider derives this candidate from deployment and telemetry evidence. "
                        "Use a real LLM provider for deeper causal reasoning."
                    ),
                    "grounding": "inferred",
                    "supporting_evidence": candidate_refs,
                    "contradicting_evidence": [],
                    "uncertainty": "Demo provider does not perform full causal analysis.",
                }
            ],
            "most_likely_root_cause": {
                "title": "Needs LLM investigation",
                "explanation": "The evidence packet is valid, but deterministic demo mode should not be treated as a real incident autopsy.",
                "grounding": "heuristic",
                "supporting_evidence": evidence_refs[:2],
                "contradicting_evidence": [],
                "uncertainty": "Switch MODEL_PROVIDER to ollama or openai_compatible for model-generated analysis.",
            },
            "blast_radius": f"Evidence references services in the {alert.get('environment', 'unknown')} environment: {service}.",
            "evidence_summary": f"{len(logs)} logs, {len(metrics)} metrics, {len(deployments)} deployments, {len(traces)} traces.",
            "contributing_factors": ["Deterministic demo mode cannot verify contributing factors beyond provided evidence shape."],
            "prevention_actions": [
                {
                    "priority": "p1",
                    "action": "Run INCIDENT_AUTOPSY with an LLM provider before using this report operationally.",
                    "rationale": "Demo mode validates the pipeline but does not provide real model-generated reasoning.",
                    "related_evidence": evidence_refs[:2],
                }
            ],
            "follow_up_questions": ["Which real provider/model should investigate this evidence packet?"],
            "postmortem_markdown": f"## {service} incident\n\nDemo mode validated evidence ingestion for `{alert_id}`.",
            "grounding_notes": "This output is deterministic demo analysis, not a true LLM-generated autopsy.",
            "analysis_limitations": ["Deterministic demo provider used; causal reasoning is intentionally limited."],
        }

    def _review_pr(self, diff: str) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        logger.info(
            "demo_pr_review_started",
            extra={
                "provider": self.provider_name,
                "runtime_mode": "deterministic_demo",
                "diff_chars": len(diff),
                "diff_lines": diff.count("\n") + 1 if diff else 0,
            },
        )

        if "select id, email, role, password_hash" in diff or "where email = '{q}'" in diff:
            logger.info(
                "demo_pattern_matched",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "pattern": "user_sql_interpolation",
                    "runtime_mode": "deterministic_demo",
                },
            )
            issues.append(
                {
                    "severity": "high",
                    "category": "security",
                    "grounding": "grounded",
                    "title": "User-controlled SQL is interpolated into the query",
                    "file": "backend/app/api/users.py",
                    "line": 14,
                    "end_line": 15,
                    "evidence": "The search endpoint builds SQL with an f-string using q and also returns password_hash.",
                    "reasoning": "A caller can inject SQL through q, and the result exposes authentication internals across the API boundary.",
                    "suggested_fix": "Use parameterized SQL or an ORM query builder and return only id, email, and role fields.",
                    "skill_references": [
                        "Database Conventions: Use parameterized queries or ORM query builders for all user-controlled values.",
                        "Database Conventions: Do not return password hashes, access tokens, refresh tokens, or internal auth fields from API responses.",
                    ],
                }
            )

        if "ADMIN_PASSWORD" in diff or "send_welcome_email(user.email, ADMIN_PASSWORD)" in diff:
            logger.info(
                "demo_pattern_matched",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "pattern": "hardcoded_admin_password",
                    "runtime_mode": "deterministic_demo",
                },
            )
            issues.append(
                {
                    "severity": "high",
                    "category": "security",
                    "grounding": "grounded",
                    "title": "Password reset flow introduces a hardcoded plain text password",
                    "file": "backend/app/api/users.py",
                    "line": 10,
                    "end_line": 24,
                    "evidence": "ADMIN_PASSWORD is hardcoded and later sent by email during reset_password.",
                    "reasoning": "This creates a reusable shared credential, stores it as a password hash value, and transmits the secret over email.",
                    "suggested_fix": "Generate a short-lived reset token, store only a hashed token, and send a reset link instead of a password.",
                    "skill_references": [
                        "Authentication Rules: Never store or send plain text passwords.",
                        "Authentication Rules: Secrets must come from environment variables or a managed secret store.",
                    ],
                }
            )

        if "from app.integrations.slack_client import SlackClient" in diff:
            logger.info(
                "demo_pattern_matched",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "pattern": "route_instantiates_slack_client",
                    "runtime_mode": "deterministic_demo",
                },
            )
            issues.append(
                {
                    "severity": "low",
                    "category": "maintainability",
                    "grounding": "grounded",
                    "title": "Route handler instantiates an integration client directly",
                    "file": "backend/app/api/users.py",
                    "line": 31,
                    "end_line": 33,
                    "evidence": "notify_user imports SlackClient inside the API route and posts directly.",
                    "reasoning": "This bypasses the service boundary, makes the route harder to test, and couples API behavior to a concrete infrastructure client.",
                    "suggested_fix": "Move Slack notification behind an application service and inject that service into the route.",
                    "skill_references": [
                        "Architecture Rules: API route handlers may orchestrate application services but must not instantiate infrastructure clients directly.",
                        "Architecture Rules: Integrations must live behind service-layer abstractions.",
                    ],
                }
            )

        decision = "request_changes" if any(issue["severity"] in {"critical", "high"} for issue in issues) else "approve"
        summary = (
            "Request changes. The diff introduces directly observable SQL injection, credential handling violations, "
            "and a lower-severity service-boundary issue."
            if issues
            else "No material issues were detected in the diff."
        )

        result = {
            "mode": "PR_AUTOPILOT",
            "decision": decision,
            "summary": summary,
            "issues": issues,
            "reviewer_notes": [
                "All PR findings are grounded in added diff lines; no heuristic findings are included.",
                "The security issues are release-blocking because the added code directly exposes credential material and interpolates request-controlled values into SQL. They are high severity rather than critical because the demo diff does not prove broader system compromise.",
                "The maintainability issue is lower severity because it affects testability without crossing a direct security boundary.",
            ]
            if issues
            else [],
        }
        logger.info(
            "demo_pr_review_completed",
            extra={
                "mode": "PR_AUTOPILOT",
                "provider": self.provider_name,
                "runtime_mode": "deterministic_demo",
                "decision": decision,
                "findings": len(issues),
                "grounded": sum(1 for issue in issues if issue.get("grounding") == "grounded"),
            },
        )
        return result

    def _autopsy_incident(self, logs: str) -> dict[str, Any]:
        return {
            "mode": "INCIDENT_AUTOPSY",
            "severity": "sev2",
            "executive_summary": (
                "The dashboard incident began with a traffic spike that amplified an existing N+1 query path. "
                "Database connections saturated, request latency climbed, and dashboard requests returned 503s until rollback."
            ),
            "root_cause": (
                "An N+1 dashboard data-loading path generated hundreds of queries per request under elevated traffic, "
                "exhausting the Postgres connection pool."
            ),
            "causal_chain": [
                "Request rate rose from 240rps to 780rps on /dashboard.",
                "Dashboard requests began issuing hundreds of database queries per render.",
                "The Postgres pool reached 20/20 active connections and checkout waits climbed to 5000ms.",
                "API workers timed out waiting for database connections and returned 503 responses.",
                "Rollback restored the previous data-loading behavior and latency returned to normal.",
            ],
            "timeline": [
                {
                    "timestamp": "2026-05-06T09:00:01Z",
                    "event": "Dashboard operating normally",
                    "evidence": "request_rate=240rps p95_ms=180 status=200",
                },
                {
                    "timestamp": "2026-05-06T09:01:14Z",
                    "event": "Traffic spike begins",
                    "evidence": "request_rate=780rps route=/dashboard p95_ms=410",
                },
                {
                    "timestamp": "2026-05-06T09:02:22Z",
                    "event": "N+1 symptoms appear",
                    "evidence": "query_count=312 duration_ms=2800",
                },
                {
                    "timestamp": "2026-05-06T09:03:18Z",
                    "event": "Connection pool is exhausted",
                    "evidence": "pool_in_use=20 pool_size=20 wait_ms=5000",
                },
                {
                    "timestamp": "2026-05-06T09:03:19Z",
                    "event": "User-visible failures start",
                    "evidence": "status=503 QueuePool limit of size 20 overflow 0 reached",
                },
                {
                    "timestamp": "2026-05-06T09:07:45Z",
                    "event": "Rollback is executed",
                    "evidence": "deploy action=rollback version=2026.05.06.1 previous=2026.05.05.4",
                },
                {
                    "timestamp": "2026-05-06T09:09:12Z",
                    "event": "Service recovers",
                    "evidence": "request_rate=310rps p95_ms=340 status=200",
                },
            ],
            "post_mortem": {
                "impact": "Dashboard users saw elevated latency and 503 responses for roughly six minutes.",
                "root_cause": "N+1 query amplification on the dashboard path exhausted the Postgres connection pool during a traffic spike.",
                "contributing_factors": [
                    "Dashboard rendering allowed unbounded related-record lookups.",
                    "No query-count regression test blocked the inefficient data-loading path.",
                    "Connection pool alerts surfaced after saturation instead of warning on query amplification.",
                ],
                "what_went_well": [
                    "Logs contained request rate, query count, pool usage, and rollback events.",
                    "Rollback restored normal p95 latency quickly.",
                ],
                "what_went_wrong": [
                    "The system treated pool exhaustion as the primary alert, even though it was downstream of N+1 behavior.",
                    "The release path did not catch hundreds of queries per dashboard request.",
                ],
                "prevention_plan": [
                    {
                        "priority": "p0",
                        "owner": "Backend",
                        "action": "Replace per-widget dashboard lookups with eager loading or batched aggregate queries.",
                        "rationale": "Removes the N+1 path that initiated the incident.",
                    },
                    {
                        "priority": "p1",
                        "owner": "Backend",
                        "action": "Add a query-count regression test for dashboard requests under representative fixture data.",
                        "rationale": "Prevents future changes from reintroducing query amplification.",
                    },
                    {
                        "priority": "p1",
                        "owner": "SRE",
                        "action": "Alert on query_count per request and pool usage above 80 percent before checkout timeouts.",
                        "rationale": "Catches the causal signal before user-visible 503s.",
                    },
                ],
            },
            "skill_references": [
                "Database Conventions: Avoid N+1 query patterns in request handlers.",
                "Lessons From Previous Incidents: Connection pool exhaustion was a symptom, not the initiating cause.",
                "Lessons From Previous Incidents: Prevention requires query-count regression tests and eager loading.",
            ],
            "confidence": 0.96,
        }
