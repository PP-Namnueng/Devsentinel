from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.core.config import get_settings
from app.memory.skill_loader import SkillMemory
from app.model_gateway.base import ModelConfigError, ModelGatewayError, ModelOutputError
from app.model_gateway.factory import build_model_gateway
from app.orchestrator.orchestrator import DevSentinelOrchestrator
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, ModelInfo
from app.schemas.incident import IncidentAutopsyRequest, IncidentAutopsyResult
from app.schemas.pr_review import PRReviewRequest, PRReviewResult

router = APIRouter()


def _provider_error(exc: ModelGatewayError) -> HTTPException:
    status_code = 400 if isinstance(exc, ModelConfigError) else 502
    return HTTPException(status_code=status_code, detail=str(exc))


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "provider": settings.model_provider}


@router.get("/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    try:
        return await build_model_gateway().list_models()
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    skill_memory = SkillMemory().load()
    governed_request = ChatRequest(
        messages=[
            ChatMessage(role="system", content=skill_memory),
            *request.messages,
        ],
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    try:
        return await build_model_gateway().chat(governed_request)
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc


@router.post("/pr-autopilot", response_model=PRReviewResult)
def run_pr_autopilot(request: PRReviewRequest) -> PRReviewResult:
    try:
        orchestrator = DevSentinelOrchestrator()
        return orchestrator.run_pr_autopilot(request)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail={"message": "Model output failed schema validation", "errors": exc.errors()}) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/incident-autopsy", response_model=IncidentAutopsyResult)
def run_incident_autopsy(request: IncidentAutopsyRequest) -> IncidentAutopsyResult:
    try:
        orchestrator = DevSentinelOrchestrator()
        return orchestrator.run_incident_autopsy(request)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail={"message": "Model output failed schema validation", "errors": exc.errors()}) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
