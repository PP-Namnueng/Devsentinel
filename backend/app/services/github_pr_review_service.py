from __future__ import annotations

import logging

from app.integrations.github_client import GitHubClient
from app.orchestrator.orchestrator import DevSentinelOrchestrator
from app.schemas.github_pr import GitHubPRReviewRequest, GitHubPRReviewResponse
from app.schemas.pr_review import PRReviewRequest
from app.services.pr_review_comment_renderer import render_pr_review_comment

logger = logging.getLogger(__name__)


class GitHubPRReviewService:
    def __init__(
        self,
        github_client: GitHubClient | None = None,
        orchestrator: DevSentinelOrchestrator | None = None,
    ) -> None:
        self.github_client = github_client or GitHubClient()
        self.orchestrator = orchestrator or DevSentinelOrchestrator()

    def review_pull_request(self, request: GitHubPRReviewRequest) -> GitHubPRReviewResponse:
        logger.info(
            "github_pr_review_started",
            extra={
                "mode": "PR_AUTOPILOT",
                "owner": request.owner,
                "repo": request.repo,
                "pull_number": request.pull_number,
                "model": request.model,
                "post_comment": request.post_comment,
            },
        )
        diff = self.github_client.get_pull_request_diff(
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
        )
        logger.info(
            "github_pr_diff_fetched",
            extra={
                "mode": "PR_AUTOPILOT",
                "owner": request.owner,
                "repo": request.repo,
                "pull_number": request.pull_number,
                "diff_chars": len(diff),
                "diff_lines": diff.count("\n") + 1 if diff else 0,
            },
        )

        review = self.orchestrator.run_pr_autopilot(
            PRReviewRequest(
                diff=diff,
                repository_context=request.repository_context
                or f"{request.owner}/{request.repo} PR #{request.pull_number}",
                model=request.model,
            )
        )

        comment_body = render_pr_review_comment(review)
        comment_url = None
        if request.post_comment:
            logger.info(
                "github_comment_publication_started",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "owner": request.owner,
                    "repo": request.repo,
                    "pull_number": request.pull_number,
                    "comment_chars": len(comment_body),
                },
            )
            created = self.github_client.post_pull_request_comment(
                owner=request.owner,
                repo=request.repo,
                pull_number=request.pull_number,
                body=comment_body,
            )
            comment_url = created.get("html_url")
            logger.info(
                "github_comment_publication_completed",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "owner": request.owner,
                    "repo": request.repo,
                    "pull_number": request.pull_number,
                    "posted_to_github": True,
                    "github_comment_url": comment_url,
                },
            )
        else:
            logger.info(
                "github_comment_publication_skipped",
                extra={
                    "mode": "PR_AUTOPILOT",
                    "owner": request.owner,
                    "repo": request.repo,
                    "pull_number": request.pull_number,
                    "posted_to_github": False,
                },
            )

        return GitHubPRReviewResponse(
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
            model=request.model,
            review=review,
            comment_body=comment_body,
            posted_to_github=request.post_comment,
            github_comment_url=comment_url,
        )
