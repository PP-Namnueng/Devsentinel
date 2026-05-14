# DevSentinel

DevSentinel is a hackathon-focused AI Engineering Intelligence Platform scoped to two modes:

- PR Autopilot: senior-engineer style PR diff review.
- Incident Autopsy: causal incident analysis from pasted production logs.

Phase 1 stabilizes the model gateway runtime. The default provider is `demo`, which is deterministic and safe for a five-minute hackathon presentation. Real providers can be enabled with `MODEL_PROVIDER=openai_compatible` or `MODEL_PROVIDER=ollama`.

## Project Layout

```text
devsentinel/
├── docs/
├── artifacts/
├── backend/
│   └── app/
│       ├── api/
│       ├── orchestrator/
│       ├── modes/
│       ├── prompts/
│       ├── schemas/
│       ├── memory/
│       ├── model_gateway/
│       └── integrations/
├── frontend/
├── ml/
└── scripts/
```

## Backend

```powershell
cd devsentinel/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open API docs at `http://localhost:8000/docs`.

### Demo Mode

```env
MODEL_PROVIDER=demo
REQUEST_TIMEOUT_SECONDS=60
DEFAULT_TEMPERATURE=0.0
SKILL_PATH=artifacts/SKILL.md
```

### OpenAI-Compatible Mode

OpenAI:

```env
MODEL_PROVIDER=openai_compatible
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
SKILL_PATH=artifacts/SKILL.md
```

OpenRouter:

```env
MODEL_PROVIDER=openai_compatible
OPENAI_API_KEY=sk-or-your_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
SKILL_PATH=artifacts/SKILL.md
```

`OPENAI_BASE_URL` can point to any provider that supports OpenAI-compatible `/chat/completions`. `MODEL_PROVIDER=openai` is still accepted as a backward-compatible alias, but new demos should use `openai_compatible`.

### Ollama Mode

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
SKILL_PATH=artifacts/SKILL.md
```

Pull the model first:

```powershell
ollama pull llama3.1
```

### Runtime API Checks

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/models
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Explain DevSentinel Phase 1 in one sentence.\"}],\"temperature\":0,\"max_tokens\":128}"
```

Chat without a model uses the provider default from `.env`:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"messages":[{"role":"user","content":"Explain DevSentinel Phase 1 in one sentence."}],"temperature":0,"max_tokens":128}'
```

Chat with a runtime model override:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"model":"llama3.1","messages":[{"role":"user","content":"Explain DevSentinel Phase 1 in one sentence."}],"temperature":0,"max_tokens":128}'
```

The same runtime endpoints are also available under `/api` for compatibility, for example `http://localhost:8000/api/health`.

### GitHub PR Autopilot

GitHub PR review uses the existing PR Autopilot mode, but fetches the diff from GitHub and can post the generated Markdown review as a PR comment.

```env
GITHUB_TOKEN=
GITHUB_API_BASE_URL=https://api.github.com
```

For classic personal access tokens, use a token with repo access for private repositories. The token must be able to read pull requests and create issue comments.

Preview without posting:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/github/pr-review `
  -ContentType "application/json" `
  -Body '{"owner":"my-org","repo":"my-repo","pull_number":12,"model":"gpt-4.1-mini","repository_context":"FastAPI backend service","post_comment":false}'
```

### Incident Evidence Providers

Incident Autopsy can still run from pasted logs or deterministic fixtures, but `/api/incidents/webhook` now resolves evidence through a provider factory. The model never calls observability tools directly. Backend adapters fetch bounded evidence, normalize it into `IncidentEvidencePacket`, redact common secrets, and then the mode analyzes that packet.

Demo fixtures:

```env
INCIDENT_EVIDENCE_PROVIDER=fixture
```

Local log file testing:

```env
INCIDENT_EVIDENCE_PROVIDER=local_file
INCIDENT_LOG_FILE_PATH=app/log_sources/dashboard-api.log
INCIDENT_LOG_LIMIT=200
```

Datadog evidence:

```env
INCIDENT_EVIDENCE_PROVIDER=datadog
DATADOG_API_KEY=your_api_key
DATADOG_APP_KEY=your_app_key
DATADOG_SITE=datadoghq.com
INCIDENT_LOG_LIMIT=200
```

Loki and Prometheus evidence:

```env
INCIDENT_EVIDENCE_PROVIDER=loki_prometheus
LOKI_BASE_URL=http://localhost:3100
PROMETHEUS_BASE_URL=http://localhost:9090
INCIDENT_LOG_LIMIT=200
```

Webhook alerts can override the configured provider with `evidence_provider` or `labels.evidence_provider`. The supported values are `fixture`, `local_file`, `datadog`, and `loki_prometheus`.

Test the configured evidence datasource without running model analysis:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/incidents/evidence/test `
  -ContentType "application/json" `
  -Body '{"provider":"loki_prometheus","loki_base_url":"http://localhost:3100","prometheus_base_url":"http://localhost:9090","log_limit":200}'
```

Grafana Alerting can call the Grafana-specific webhook adapter:

```text
POST http://localhost:8000/api/incidents/grafana-webhook
```

Required Grafana alert labels:

```text
service=dashboard-api
environment=production
severity=sev2
```

The adapter accepts Grafana's default webhook payload, extracts the firing alert, converts it to `AlertContext`, sets `evidence_provider=loki_prometheus`, and then runs the same incident evidence and analysis pipeline.

Minimal Grafana webhook test payload:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/incidents/grafana-webhook `
  -ContentType "application/json" `
  -Body '{
    "receiver":"devsentinel",
    "status":"firing",
    "title":"High error rate",
    "alerts":[{
      "status":"firing",
      "startsAt":"2026-05-09T10:00:00Z",
      "fingerprint":"grafana-dashboard-api-errors",
      "labels":{
        "alertname":"High error rate",
        "service":"dashboard-api",
        "environment":"production",
        "severity":"sev2"
      },
      "annotations":{
        "summary":"dashboard-api is returning elevated 5xx responses"
      }
    }]
  }'
```

### Provider Test Commands

Demo provider:

```powershell
$env:MODEL_PROVIDER="demo"
uvicorn app.main:app --reload --port 8000
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/models
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"messages":[{"role":"user","content":"Demo runtime check"}],"temperature":0}'
```

Ollama provider with dynamic model discovery:

```powershell
$env:MODEL_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="llama3.1"
ollama list
Invoke-RestMethod http://localhost:8000/models
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"messages":[{"role":"user","content":"Ollama runtime check"}],"temperature":0}'
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"model":"qwen2.5:latest","messages":[{"role":"user","content":"Use the requested model override."}],"temperature":0}'
```

`GET /models` calls Ollama's `/api/tags` endpoint and returns installed models as `{"id": "...", "provider": "ollama"}`.

OpenAI-compatible provider:

```powershell
$env:MODEL_PROVIDER="openai_compatible"
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
Invoke-RestMethod http://localhost:8000/models
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"messages":[{"role":"user","content":"OpenAI-compatible runtime check"}],"temperature":0,"max_tokens":128}'
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Use this runtime model override."}],"temperature":0,"max_tokens":128}'
```

OpenRouter:

```powershell
$env:MODEL_PROVIDER="openai_compatible"
$env:OPENAI_API_KEY="sk-or-your_api_key"
$env:OPENAI_BASE_URL="https://openrouter.ai/api/v1"
$env:OPENAI_MODEL="openai/gpt-4o-mini"
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod -Method Post http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"OpenRouter runtime check"}],"temperature":0,"max_tokens":128}'
```

## Frontend

```powershell
cd devsentinel/frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Demo Inputs

- `artifacts/sample_pr.diff`: SQL injection, plain text password handling, and architecture violation.
- `artifacts/sample_logs.txt`: traffic spike, N+1 query symptoms, and connection pool exhaustion.
- `artifacts/SKILL.md`: database conventions, auth rules, architecture rules, and prior incident lessons.

## Validation

```powershell
cd devsentinel
python scripts/smoke_test.py
```

## Phase 1 Architecture

FastAPI owns the HTTP surface, Pydantic validates inputs and outputs, and the model gateway hides provider details behind `chat()`, `list_models()`, and the existing mode-oriented `generate_json()`. `artifacts/SKILL.md` is loaded as engineering governance memory and injected into chat/system prompts so demo behavior stays consistent.
