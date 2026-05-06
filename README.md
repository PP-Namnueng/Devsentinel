# DevSentinel

DevSentinel is a hackathon-focused AI Engineering Intelligence Platform scoped to two modes:

- PR Autopilot: senior-engineer style PR diff review.
- Incident Autopsy: causal incident analysis from pasted production logs.

Phase 1 stabilizes the model gateway runtime. The default provider is `demo`, which is deterministic and safe for a five-minute hackathon presentation. Real providers can be enabled with `MODEL_PROVIDER=openai` or `MODEL_PROVIDER=ollama`.

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
SKILL_PATH=artifacts/SKILL.md
```

### OpenAI-Compatible Mode

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
SKILL_PATH=artifacts/SKILL.md
```

`OPENAI_BASE_URL` can point to any provider that supports OpenAI-compatible `/chat/completions`.

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

The same runtime endpoints are also available under `/api` for compatibility, for example `http://localhost:8000/api/health`.

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
