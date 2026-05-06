# DevSentinel Engineering Memory

## Core Engineering Principles

- Prefer deterministic and explainable behavior over hidden complexity.
- Optimize for maintainability before clever abstractions.
- Keep orchestration explicit and operationally observable.
- Prefer minimal safe architectural changes during incident mitigation.
- Reduce operational complexity where possible.
- Security-sensitive changes require conservative review standards.

## Constraints

- Do not invent missing implementation details.
- Explicitly label assumptions when evidence is incomplete.
- Distinguish observed behavior from inferred causes.
- Avoid speculative conclusions without observable signals.
- Do not recommend architectural rewrites unless operationally necessary.

## Severity Policy

- Credential exposure is always Critical severity.
- Authentication bypass risks require Request Changes.
- Data corruption risks are High severity.
- Infrastructure boundary violations are High severity.
- Architecture violations are Medium severity unless they cross security boundaries.
- Performance risks become High severity when they threaten operational stability.

## Security Rules

- Never expose secrets, credentials, internal tokens, or sensitive infrastructure metadata in logs or API responses.
- Treat all external input as untrusted until validated.
- Security-sensitive changes require conservative review and explicit justification.
- Enforce least-privilege access patterns for integrations and infrastructure clients.
- Avoid bypassing service-layer validation or authorization boundaries.
- Infrastructure and credential handling logic must remain isolated from presentation layers.
- Prefer explicit validation over implicit trust assumptions.
- Escalate potential data exposure risks even when exploitability is uncertain.

## Database Conventions

- Use parameterized queries or ORM query builders for all user-controlled values.
- Do not return password hashes, access tokens, refresh tokens, or internal auth fields from API responses.
- Avoid N+1 query patterns in request handlers. Batch-load related data and cap query count for dashboard endpoints.
- Keep database connection pool usage below 80 percent during normal traffic.

## API Contract Rules

- All API responses crossing service boundaries must use validated Pydantic schemas.
- Avoid returning unvalidated dictionaries across service boundaries.
- Preserve backward compatibility unless APIs are explicitly versioned.
- API handlers should return structured response models instead of raw infrastructure outputs.
- Schema validation failures should be treated as operational defects, not ignored warnings.

## Authentication Rules

- Never store or send plain text passwords.
- Password reset flows must create short-lived reset tokens and send reset links, not passwords.
- Secrets must come from environment variables or a managed secret store.
- Auth-related changes require request-change severity when they expose credentials or bypass policy.

## Architecture Rules

- API route handlers may orchestrate application services but must not instantiate infrastructure clients directly.
- Integrations must live behind service-layer abstractions.
- Backend outputs crossing API boundaries must be validated with Pydantic schemas.
- Keep orchestration explicit and simple. Do not introduce graph workflows for two-mode routing.

## Incident Analysis Methodology

- Reconstruct the initiating cause before evaluating downstream failures.
- Separate triggering events from amplification effects.
- Prioritize operationally actionable remediations.
- Correlate infrastructure symptoms with application-level behavior.

## Lessons From Previous Incidents

- The May dashboard outage was caused by traffic amplification of an N+1 query path.
- Connection pool exhaustion was a symptom, not the initiating cause.
- Prevention requires query-count regression tests and eager loading for dashboard aggregate data.
- Incident reviews should reconstruct the causal chain before listing remediations.

## Review Philosophy

- Prioritize deterministic and explainable fixes over clever abstractions.
- Prefer minimal architectural changes during incident mitigation.
- Recommend fixes that reduce operational complexity.
- When uncertain, explicitly state assumptions and missing evidence.

## Output Expectations

- Findings must be concise and evidence-based.
- Avoid speculative conclusions without observable signals.
- Separate root causes from secondary symptoms.
- Prefer structured outputs over narrative-heavy responses.
- Include confidence levels for critical conclusions.
