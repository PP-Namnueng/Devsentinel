from app.model_gateway.base import ModelGateway
from app.prompts.pr_review import build_pr_review_prompt
from app.schemas.pr_review import PRReviewRequest, PRReviewResult


class PRAutopilotMode:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def analyze(self, request: PRReviewRequest, skill_memory: str) -> PRReviewResult:
        prompt = build_pr_review_prompt(
            diff=request.diff,
            skill_memory=skill_memory,
            repository_context=request.repository_context,
        )
        raw = self.gateway.generate_json(
            mode="PR_AUTOPILOT",
            prompt=prompt,
            inputs={
                "diff": request.diff,
                "repository_context": request.repository_context,
                "skill_memory": skill_memory,
            },
        )
        return PRReviewResult.model_validate(raw)
