from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.orchestrator.orchestrator import DevSentinelOrchestrator
from app.schemas.incident import IncidentAutopsyRequest
from app.schemas.pr_review import PRReviewRequest


def main() -> None:
    artifacts = ROOT / "artifacts"
    diff = (artifacts / "sample_pr.diff").read_text(encoding="utf-8")
    logs = (artifacts / "sample_logs.txt").read_text(encoding="utf-8")

    orchestrator = DevSentinelOrchestrator()
    review = orchestrator.run_pr_autopilot(PRReviewRequest(diff=diff))
    autopsy = orchestrator.run_incident_autopsy(IncidentAutopsyRequest(logs=logs))

    assert review.decision == "request_changes"
    assert len(review.issues) >= 3
    assert autopsy.severity == "sev2"
    assert len(autopsy.causal_chain) >= 5

    print("smoke_test: ok")


if __name__ == "__main__":
    main()
