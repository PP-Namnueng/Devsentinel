from __future__ import annotations

from app.memory.skill_loader import SkillMemory
from app.model_gateway.base import ModelGateway
from app.model_gateway.factory import build_model_gateway
from app.modes.incident_autopsy import IncidentAutopsyMode
from app.modes.pr_autopilot import PRAutopilotMode
from app.schemas.incident import IncidentAutopsyRequest, IncidentAutopsyResult
from app.schemas.pr_review import PRReviewRequest, PRReviewResult


class DevSentinelOrchestrator:
    """Simple two-mode router for the locked hackathon scope."""

    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.memory = SkillMemory()
        self.gateway = gateway or build_model_gateway()
        self.pr_mode = PRAutopilotMode(self.gateway)
        self.incident_mode = IncidentAutopsyMode(self.gateway)

    def run_pr_autopilot(self, request: PRReviewRequest) -> PRReviewResult:
        skill = self.memory.load(request.skill_path)
        return self.pr_mode.analyze(request, skill)

    def run_incident_autopsy(self, request: IncidentAutopsyRequest) -> IncidentAutopsyResult:
        skill = self.memory.load(request.skill_path)
        return self.incident_mode.analyze(request, skill)
