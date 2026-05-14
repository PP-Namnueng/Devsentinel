from __future__ import annotations

from app.schemas.pr_review import PRReviewIssue, PRReviewResult


SEVERITY_LABELS = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]",
    "medium": "[MEDIUM]",
    "low": "[LOW]",
}


def render_pr_review_comment(review: PRReviewResult) -> str:
    lines = [
        "## DevSentinel PR Autopilot",
        "",
        f"**Decision:** {review.decision}",
        f"**Summary:** {review.summary}",
        "",
    ]

    if review.issues:
        lines.extend(["### Findings", ""])
        for issue in review.issues:
            lines.extend(_render_issue(issue))
    else:
        lines.extend(
            [
                "### Findings",
                "",
                "No blocking findings were detected. DevSentinel recommends approval based on the provided diff.",
                "",
            ]
        )

    if review.reviewer_notes:
        lines.extend(["### Reviewer Notes", ""])
        lines.extend(f"* {note}" for note in review.reviewer_notes)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _render_issue(issue: PRReviewIssue) -> list[str]:
    severity_label = SEVERITY_LABELS.get(issue.severity, "[ISSUE]")
    heading = f"#### {severity_label} {issue.category.title()}"
    lines = [
        heading,
        f"**Title:** {issue.title}",
        f"**Grounding:** {issue.grounding}",
        "",
    ]

    if issue.file:
        lines.append(f"**File:** `{issue.file}`")
    if issue.line:
        line_label = f"{issue.line}-{issue.end_line}" if issue.end_line and issue.end_line != issue.line else str(issue.line)
        lines.append(f"**Line:** {line_label}")
    if issue.file or issue.line:
        lines.append("")

    if issue.evidence:
        lines.extend(["**Evidence**", "```text", issue.evidence, "```", ""])

    lines.extend(
        [
            "**Reasoning**",
            issue.reasoning or "No reasoning provided.",
            "",
            "**Suggested Fix**",
            issue.suggested_fix or "No suggested fix provided.",
            "",
            "---",
            "",
        ]
    )
    return lines
