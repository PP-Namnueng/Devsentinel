import logging
from time import perf_counter

from pydantic import ValidationError

from app.model_gateway.base import ModelGateway
from app.prompts.pr_review import build_pr_review_prompt
from app.schemas.pr_review import (
    PRReviewGroundingStats,
    PRReviewRequest,
    PRReviewResult,
    PRReviewRuntime,
)

logger = logging.getLogger(__name__)


class PRAutopilotMode:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def analyze(
        self,
        request: PRReviewRequest,
        skill_memory: str,
    ) -> PRReviewResult:
        started_at = perf_counter()
        diff_lines = request.diff.count("\n") + 1
        repository = request.repository_context or None
        logger.info(
            "pr_review_started",
            extra={
                "mode": "PR_AUTOPILOT",
                "repository": repository,
                "diff_chars": len(request.diff),
                "diff_lines": diff_lines,
                "gateway": self.gateway.__class__.__name__,
                "model": request.model,
            },
        )

        prompt = build_pr_review_prompt(
            diff=request.diff,
            skill_memory=skill_memory,
            repository_context=request.repository_context,
        )
        logger.info(
            "prompt_generated",
            extra={
                "mode": "PR_AUTOPILOT",
                "prompt_chars": len(prompt),
                "skill_memory_attached": bool(skill_memory.strip()),
                "skill_memory_chars": len(skill_memory),
            },
        )

        raw = self.gateway.generate_json(
            mode="PR_AUTOPILOT",
            model=request.model,
            prompt=prompt,
            inputs={
                "diff": request.diff,
                "repository_context": request.repository_context,
                "skill_memory": skill_memory,
            },
        )
        logger.info(
            "schema_validation_started",
            extra={
                "mode": "PR_AUTOPILOT",
                "schema": PRReviewResult.__name__,
            },
        )

        try:
            review = PRReviewResult.model_validate(raw)
        except ValidationError as exc:
            invalid_fields = [
                ".".join(str(part) for part in error["loc"])
                for error in exc.errors()
            ]
            logger.error(
                "schema_validation_failed",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "schema": PRReviewResult.__name__,
                    "invalid_fields": invalid_fields,
                    "error_count": len(invalid_fields),
                },
            )
            raise

        logger.info(
            "schema_validation_succeeded",
            extra={
                "mode": "PR_AUTOPILOT",
                "schema": PRReviewResult.__name__,
            },
        )
        grounding_counts = {
            "grounded": 0,
            "inferred": 0,
            "heuristic": 0,
            "needs_verification": 0,
        }
        for issue in review.issues:
            grounding_counts[issue.grounding] += 1
        provider = getattr(self.gateway, "provider_name", "unknown")
        latency_ms = getattr(self.gateway, "last_generation_latency_ms", None)
        review.runtime = PRReviewRuntime(
            provider=provider,
            runtime_mode="deterministic_demo" if provider == "demo" else "llm",
            gateway=self.gateway.__class__.__name__,
            model=request.model,
            schema_name=PRReviewResult.__name__,
            schema_validation_status="passed",
            latency_ms=latency_ms,
            latency_seconds=round(latency_ms / 1000, 3) if latency_ms is not None else None,
            grounding_stats=PRReviewGroundingStats(**grounding_counts),
        )

        logger.info(
            "pr_review_completed",
            extra={
                "mode": "PR_AUTOPILOT",
                "decision": review.decision,
                "findings": len(review.issues),
                "grounded": grounding_counts["grounded"],
                "inferred": grounding_counts["inferred"],
                "heuristic": grounding_counts["heuristic"],
                "needs_verification": grounding_counts["needs_verification"],
                "latency_ms": round((perf_counter() - started_at) * 1000),
                "status": "success",
            },
        )
        return review
