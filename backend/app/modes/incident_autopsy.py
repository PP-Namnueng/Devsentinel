from app.model_gateway.base import ModelGateway
from app.prompts.incident_autopsy import build_incident_autopsy_prompt
from app.schemas.incident import IncidentAutopsyRequest, IncidentAutopsyResult


class IncidentAutopsyMode:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def analyze(self, request: IncidentAutopsyRequest, skill_memory: str) -> IncidentAutopsyResult:
        prompt = build_incident_autopsy_prompt(
            logs=request.logs,
            skill_memory=skill_memory,
            service_context=request.service_context,
        )
        raw = self.gateway.generate_json(
            mode="INCIDENT_AUTOPSY",
            prompt=prompt,
            inputs={
                "logs": request.logs,
                "service_context": request.service_context,
                "skill_memory": skill_memory,
            },
        )
        return IncidentAutopsyResult.model_validate(raw)
