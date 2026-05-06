# DevSentinel Demo Plan

DevSentinel is scoped to two modes for the hackathon demo:

1. PR Autopilot: review a pasted diff like a senior engineer.
2. Incident Autopsy: explain production failures from pasted logs.

The demo should use `artifacts/sample_pr.diff`, `artifacts/sample_logs.txt`, and `artifacts/SKILL.md` for deterministic, repeatable behavior.

## Five-Minute Flow

1. Show the product interface with two modes only.
2. Run PR Autopilot against `sample_pr.diff`.
3. Highlight SQL injection, plain text password handling, and architecture violation.
4. Run Incident Autopsy against `sample_logs.txt`.
5. Highlight the causal chain: traffic spike -> N+1 query amplification -> pool exhaustion -> 503s.
6. Close with the memory angle: both modes cite engineering conventions and incident lessons from `SKILL.md`.

## Reliability Choices

- Use Pydantic validation for every model-facing output.
- Keep default backend behavior deterministic through a demo gateway.
- Keep the model gateway model-agnostic so local or hosted coder models can be swapped in later.
- Avoid extra modes, autonomous planning, and graph orchestration.
