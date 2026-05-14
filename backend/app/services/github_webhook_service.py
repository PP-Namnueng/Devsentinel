from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

from app.core.config import Settings, default_review_model, get_settings
from app.schemas.github_pr import (
    GitHubPRReviewRequest,
    GitHubWebhookReviewResponse,
)
from app.services.github_pr_review_service import GitHubPRReviewService
from app.services.runtime_config_service import RuntimeConfigService

logger = logging.getLogger(__name__)

SUPPORTED_EVENT = "pull_request"
SUPPORTED_ACTIONS = {"opened", "synchronize", "reopened"}
DELIVERY_TTL_SECONDS = 60 * 60
_seen_deliveries: dict[str, float] = {}


class GitHubWebhookError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class GitHubWebhookService:
    def __init__(
        self,
        review_service: GitHubPRReviewService | None = None,
        runtime_config_service: RuntimeConfigService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.review_service = review_service or GitHubPRReviewService()
        self.runtime_config_service = runtime_config_service or RuntimeConfigService()
        self.settings = settings or get_settings()

    def handle_webhook(
        self,
        *,
        event: str | None,
        delivery_id: str | None,
        signature: str | None,
        body: bytes,
        payload: dict[str, Any],
    ) -> GitHubWebhookReviewResponse:
        self._verify_signature(signature=signature, body=body)
        action = payload.get("action")
        logger.info(
            "github_webhook_received",
            extra={
                "event": event,
                "action": action,
                "delivery_id": delivery_id,
            },
        )

        if event != SUPPORTED_EVENT:
            return self._ignored(
                reason="unsupported_event",
                event=event,
                action=action,
                delivery_id=delivery_id,
            )

        if action not in SUPPORTED_ACTIONS:
            return self._ignored(
                reason="unsupported_action",
                event=event,
                action=action,
                delivery_id=delivery_id,
            )

        if delivery_id and self._is_duplicate_delivery(delivery_id):
            logger.info(
                "github_webhook_duplicate",
                extra={
                    "event": event,
                    "action": action,
                    "delivery_id": delivery_id,
                },
            )
            return GitHubWebhookReviewResponse(
                status="duplicate",
                reason="delivery_already_processed",
                event=event,
                action=action,
                delivery_id=delivery_id,
            )

        repository = payload.get("repository")
        pull_request = payload.get("pull_request")
        if not isinstance(repository, dict) or not isinstance(pull_request, dict):
            raise GitHubWebhookError("Webhook payload is missing repository or pull_request.", status_code=400)

        owner = self._extract_owner(repository)
        repo = repository.get("name")
        pull_number = pull_request.get("number")
        if not owner or not repo or not isinstance(pull_number, int):
            raise GitHubWebhookError("Webhook payload does not identify owner, repo, and pull request number.", status_code=400)

        runtime_route = self.runtime_config_service.get_route("PR_AUTOPILOT")
        model = runtime_route.model if runtime_route and runtime_route.model else default_review_model(self.settings)
        logger.info(
            "github_webhook_review_triggered",
            extra={
                "event": event,
                "action": action,
                "delivery_id": delivery_id,
                "owner": owner,
                "repo": repo,
                "pull_number": pull_number,
                "model": model,
                "model_source": "runtime_config" if runtime_route and runtime_route.model else "settings_fallback",
            },
        )
        review = self.review_service.review_pull_request(
            GitHubPRReviewRequest(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                model=model,
                repository_context=f"{owner}/{repo} PR #{pull_number}",
                post_comment=True,
            )
        )

        if delivery_id:
            _seen_deliveries[delivery_id] = time.time()

        return GitHubWebhookReviewResponse(
            status="accepted",
            event=event,
            action=action,
            delivery_id=delivery_id,
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            review=review,
        )

    def _verify_signature(self, signature: str | None, body: bytes) -> None:
        secret = self.settings.github_webhook_secret
        if not secret:
            raise GitHubWebhookError("GITHUB_WEBHOOK_SECRET is required for GitHub webhooks.", status_code=400)
        if not signature or not signature.startswith("sha256="):
            raise GitHubWebhookError("Missing or unsupported GitHub webhook signature.", status_code=401)

        expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            logger.warning("github_webhook_signature_failed")
            raise GitHubWebhookError("GitHub webhook signature verification failed.", status_code=401)

    def _is_duplicate_delivery(self, delivery_id: str) -> bool:
        now = time.time()
        expired = [key for key, seen_at in _seen_deliveries.items() if now - seen_at > DELIVERY_TTL_SECONDS]
        for key in expired:
            _seen_deliveries.pop(key, None)
        return delivery_id in _seen_deliveries

    def _ignored(
        self,
        *,
        reason: str,
        event: str | None,
        action: str | None,
        delivery_id: str | None,
    ) -> GitHubWebhookReviewResponse:
        logger.info(
            "github_webhook_ignored",
            extra={
                "reason": reason,
                "event": event,
                "action": action,
                "delivery_id": delivery_id,
            },
        )
        return GitHubWebhookReviewResponse(
            status="ignored",
            reason=reason,
            event=event,
            action=action,
            delivery_id=delivery_id,
        )

    def _extract_owner(self, repository: dict[str, Any]) -> str | None:
        owner = repository.get("owner")
        if isinstance(owner, dict) and isinstance(owner.get("login"), str):
            return owner["login"]
        full_name = repository.get("full_name")
        if isinstance(full_name, str) and "/" in full_name:
            return full_name.split("/", 1)[0]
        return None
