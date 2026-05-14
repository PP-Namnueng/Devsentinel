from pathlib import Path
import sys
import hashlib
import hmac
import json


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.orchestrator.orchestrator import DevSentinelOrchestrator
from app.core.config import Settings
from app.schemas.github_pr import GitHubPRReviewResponse
from app.schemas.incident import AlertContext, IncidentAutopsyRequest
from app.schemas.pr_review import PRReviewRequest
from app.schemas.runtime_config import RuntimeConfig, RuntimeRoute
from app.services.github_webhook_service import GitHubWebhookService
from app.services.incident_evidence_provider import FixtureEvidenceProvider, LocalFileEvidenceProvider


def main() -> None:
    artifacts = ROOT / "artifacts"
    diff = (artifacts / "sample_pr.diff").read_text(encoding="utf-8")
    logs = (artifacts / "sample_logs.txt").read_text(encoding="utf-8")

    orchestrator = DevSentinelOrchestrator()
    review = orchestrator.run_pr_autopilot(PRReviewRequest(diff=diff))
    autopsy = orchestrator.run_incident_autopsy(IncidentAutopsyRequest(logs=logs))
    incident_packet = FixtureEvidenceProvider().load_evidence(
        AlertContext(
            alert_id="smoke-db-saturation",
            alert_name="Database saturation",
            service="dashboard-api",
            environment="production",
            severity="sev2",
            started_at="2026-05-06T09:02:00Z",
            scenario_id="db_saturation_after_deploy",
        )
    )
    incident_report = orchestrator.run_incident_autopsy_packet(
        incident_packet,
        "devsentinel-deterministic-demo",
    )
    local_log_packet = LocalFileEvidenceProvider("app/log_sources/dashboard-api.log").load_evidence(
        AlertContext(
            alert_id="smoke-local-log",
            alert_name="Local log evidence",
            service="dashboard-api",
            environment="production",
            severity="sev2",
            started_at="2026-05-06T09:02:00Z",
            evidence_provider="local_file",
        )
    )

    assert review.decision == "request_changes"
    assert len(review.issues) >= 3
    assert autopsy.severity == "sev2"
    assert len(autopsy.causal_chain) >= 5
    assert review.runtime is not None
    assert review.runtime.schema_name == "PRReviewResult"
    assert review.runtime.grounding_stats.grounded >= 3
    assert incident_report.mode == "INCIDENT_AUTOPSY"
    assert incident_report.runtime is not None
    assert incident_report.runtime.schema_name == "IncidentAutopsyReport"
    assert incident_report.runtime.evidence_counts.logs == 5
    assert local_log_packet.source_provider == "local_file"
    assert len(local_log_packet.logs) >= 9

    webhook_payload = {
        "action": "opened",
        "repository": {
            "name": "demo-repo",
            "full_name": "demo-owner/demo-repo",
            "owner": {"login": "demo-owner"},
        },
        "pull_request": {"number": 42},
    }
    webhook_body = json.dumps(webhook_payload).encode("utf-8")
    secret = "devsentinel-test-secret"
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), webhook_body, hashlib.sha256).hexdigest()
    webhook_service = GitHubWebhookService(
        review_service=FakeGitHubReviewService(review),
        runtime_config_service=FakeRuntimeConfigService(
            RuntimeConfig(
                task_routing={
                    "PR_AUTOPILOT": RuntimeRoute(
                        provider="ollama",
                        model="runtime-config-model",
                        label="Ollama / runtime-config-model",
                    )
                }
            )
        ),
        settings=Settings(
            MODEL_PROVIDER="demo",
            GITHUB_TOKEN="test-token",
            GITHUB_WEBHOOK_SECRET=secret,
            GITHUB_WEBHOOK_DEFAULT_MODEL="env-fallback-model",
        ),
    )
    webhook_result = webhook_service.handle_webhook(
        event="pull_request",
        delivery_id="delivery-1",
        signature=signature,
        body=webhook_body,
        payload=webhook_payload,
    )
    assert webhook_result.status == "accepted"
    assert webhook_result.owner == "demo-owner"
    assert webhook_result.repo == "demo-repo"
    assert webhook_result.pull_number == 42
    assert webhook_result.review is not None
    assert webhook_result.review.model == "runtime-config-model"

    duplicate_result = webhook_service.handle_webhook(
        event="pull_request",
        delivery_id="delivery-1",
        signature=signature,
        body=webhook_body,
        payload=webhook_payload,
    )
    assert duplicate_result.status == "duplicate"

    print("smoke_test: ok")


class FakeGitHubReviewService:
    def __init__(self, review) -> None:
        self.review = review

    def review_pull_request(self, request) -> GitHubPRReviewResponse:
        return GitHubPRReviewResponse(
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
            model=request.model,
            review=self.review,
            comment_body="fake comment",
            posted_to_github=True,
            github_comment_url="https://github.example/comment/1",
        )


class FakeRuntimeConfigService:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config

    def get_route(self, task: str):
        return self.config.task_routing.get(task)


if __name__ == "__main__":
    main()
