from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


class GitHubClientError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class GitHubAuthError(GitHubClientError):
    pass


class GitHubNotFoundError(GitHubClientError):
    pass


@dataclass(frozen=True)
class GitHubClient:
    token: str | None = None
    base_url: str | None = None
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        load_dotenv(env_path, override=True)
        token = self.token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise GitHubAuthError("GITHUB_TOKEN is required to use GitHub PR review.", status_code=400)
        object.__setattr__(self, "token", token)
        object.__setattr__(self, "base_url", (self.base_url or os.getenv("GITHUB_API_BASE_URL") or "https://api.github.com").rstrip("/"))

    def get_pull_request_diff(self, owner: str, repo: str, pull_number: int) -> str:
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}",
            accept="application/vnd.github.v3.diff",
        )
        diff = response.text.strip()
        if not diff:
            raise GitHubClientError("GitHub returned an empty PR diff.", status_code=502)
        return diff

    def post_pull_request_comment(self, owner: str, repo: str, pull_number: int, body: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{pull_number}/comments",
            accept="application/vnd.github+json",
            json={"body": body},
        )
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubClientError("GitHub comment response was not valid JSON.", status_code=502) from exc

    def _request(self, method: str, path: str, accept: str, json: dict[str, Any] | None = None) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            response = httpx.request(method, url, headers=headers, json=json, timeout=self.timeout_seconds)
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"GitHub request failed: {exc}", status_code=502) from exc

        if response.status_code in {401, 403}:
            raise GitHubAuthError(
                "GitHub rejected the token or permissions. Check GITHUB_TOKEN repository access and comment permissions.",
                status_code=response.status_code,
            )
        if response.status_code == 404:
            raise GitHubNotFoundError("GitHub repository or pull request was not found.", status_code=404)
        if response.status_code >= 400:
            action = "posting PR comment" if method == "POST" else "fetching PR diff"
            raise GitHubClientError(
                f"GitHub error while {action}: HTTP {response.status_code} {response.text[:300]}",
                status_code=502,
            )

        return response
