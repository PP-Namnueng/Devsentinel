import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError

from app.core.config import default_review_model, get_settings
from app.integrations.grafana_alert_adapter import GrafanaAlertAdapter, GrafanaAlertAdapterError
from app.integrations.github_client import GitHubClientError
from app.memory.skill_loader import SkillMemory
from app.model_gateway.base import ModelConfigError, ModelGatewayError, ModelOutputError
from app.model_gateway.factory import build_model_gateway
from app.orchestrator.orchestrator import DevSentinelOrchestrator
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from app.schemas.github_pr import (
    GitHubPRReviewRequest,
    GitHubPRReviewResponse,
    GitHubWebhookReviewResponse,
)
from app.schemas.grafana import GrafanaWebhookPayload
from app.schemas.incident import AlertContext, IncidentAutopsyReport, IncidentAutopsyRequest, IncidentAutopsyResult, IncidentEvidencePacket, StoredIncident
from app.schemas.runtime_config import IncidentEvidenceConfig, RuntimeConnectionTestRequest, RuntimeConnectionTestResult
from app.schemas.pr_review import PRReviewRequest, PRReviewResult
from app.schemas.runtime_config import RuntimeConfig
from app.services.github_pr_review_service import GitHubPRReviewService
from app.services.github_webhook_service import GitHubWebhookError, GitHubWebhookService
from app.services.evidence_provider_factory import build_incident_evidence_provider
from app.services.evidence_connection_tester import EvidenceConnectionTester, EvidenceConnectionTestResult
from app.services.incident_evidence_provider import IncidentEvidenceError
from app.services.incident_store import IncidentStore
from app.services.notification_service import IncidentNotificationService
from app.services.runtime_config_service import RuntimeConfigService

router = APIRouter()
logger = logging.getLogger(__name__)


def _provider_error(exc: ModelGatewayError) -> HTTPException:
    status_code = 400 if isinstance(exc, ModelConfigError) else 502
    return HTTPException(status_code=status_code, detail=str(exc))


def _incident_model(requested_model: str | None) -> str:
    if requested_model:
        return requested_model
    route = RuntimeConfigService().get_route("INCIDENT_AUTOPSY")
    if route and route.model:
        return route.model
    return default_review_model(get_settings())


def _save_incident(alert: AlertContext, report: IncidentAutopsyReport, source: str) -> StoredIncident:
    incident = IncidentStore().save(alert=alert, report=report, source=source)
    IncidentNotificationService().notify(incident)
    return incident


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "provider": settings.model_provider}


@router.get("/models")
async def list_models() -> dict[str, object]:
    try:
        models = await build_model_gateway().list_models()
        return {
            "provider": models[0].provider if models else "unknown",
            "models": [model.id for model in models],
        }
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc


@router.get("/runtime-config", response_model=RuntimeConfig)
def get_runtime_config() -> RuntimeConfig:
    return RuntimeConfigService().load()


@router.put("/runtime-config", response_model=RuntimeConfig)
def put_runtime_config(config: RuntimeConfig) -> RuntimeConfig:
    return RuntimeConfigService().save(config)


@router.post("/runtime-config/test", response_model=RuntimeConnectionTestResult)
async def test_runtime_config(request: RuntimeConnectionTestRequest) -> RuntimeConnectionTestResult:
    try:
        gateway = build_model_gateway(runtime_provider=request.model_gateway)
        models = await gateway.list_models()
        model_ids = [model.id for model in models]
        return RuntimeConnectionTestResult(
            provider=models[0].provider if models else request.model_gateway.provider,
            ok=True,
            detail="Connection verified",
            models=model_ids,
        )
    except ModelGatewayError as exc:
        return RuntimeConnectionTestResult(
            provider=request.model_gateway.provider,
            ok=False,
            detail=str(exc),
        )


@router.get("/incidents", response_model=list[StoredIncident])
def list_incidents() -> list[StoredIncident]:
    return sorted(IncidentStore().list(), key=lambda item: item.created_at, reverse=True)


@router.get("/incidents/latest", response_model=StoredIncident | None)
def get_latest_incident() -> StoredIncident | None:
    return IncidentStore().latest()


@router.get("/incidents/{incident_id}", response_model=StoredIncident)
def get_incident(incident_id: str) -> StoredIncident:
    incident = IncidentStore().get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return incident


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
        invalid_fields = [
            ".".join(str(part) for part in error["loc"])
            for error in exc.errors()
        ]
        logger.error(
            "schema_validation_failed",
            extra={
                "mode": "PR_AUTOPILOT",
                "invalid_fields": invalid_fields,
                "error_count": len(invalid_fields),
            },
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": exc.errors(),
            },
        ) from exc

    except ModelOutputError as exc:
        logger.exception(
            "model_output_failed",
            extra={"mode": "PR_AUTOPILOT", "failure_type": "model_output"},
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except ModelGatewayError as exc:
        logger.exception(
            "provider_routing_or_inference_failed",
            extra={"mode": "PR_AUTOPILOT", "failure_type": "model_gateway"},
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except FileNotFoundError as exc:
        logger.exception(
            "skill_memory_load_failed",
            extra={"mode": "PR_AUTOPILOT", "failure_type": "file_not_found"},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/github/pr-review", response_model=GitHubPRReviewResponse)
def run_github_pr_review(request: GitHubPRReviewRequest) -> GitHubPRReviewResponse:
    try:
        return GitHubPRReviewService().review_pull_request(request)
    except GitHubClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": exc.errors(),
            },
        ) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/github/webhook", response_model=GitHubWebhookReviewResponse)
async def run_github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> GitHubWebhookReviewResponse:
    body = await request.body()
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Webhook payload must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be a JSON object.")

    try:
        return await run_in_threadpool(
            GitHubWebhookService().handle_webhook,
            event=x_github_event,
            delivery_id=x_github_delivery,
            signature=x_hub_signature_256,
            body=body,
            payload=payload,
        )
    except GitHubWebhookError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except GitHubClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValidationError as exc:
        errors: list[dict[str, Any]] = exc.errors()
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": errors,
            },
        ) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/incident-autopsy", response_model=IncidentAutopsyResult)
def run_incident_autopsy(request: IncidentAutopsyRequest) -> IncidentAutopsyResult:
    try:
        orchestrator = DevSentinelOrchestrator()
        return orchestrator.run_incident_autopsy(request)
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": exc.errors(),
            },
        ) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/incidents/webhook", response_model=IncidentAutopsyReport)
def run_incident_webhook(alert: AlertContext) -> IncidentAutopsyReport:
    try:
        packet = build_incident_evidence_provider(alert).load_evidence(alert)
        model = _incident_model(alert.model or packet.model)
        report = DevSentinelOrchestrator().run_incident_autopsy_packet(packet, model)
        _save_incident(alert, report, source=packet.source_provider)
        return report
    except IncidentEvidenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": exc.errors(),
            },
        ) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/incidents/grafana-webhook", response_model=IncidentAutopsyReport)
def run_grafana_incident_webhook(payload: GrafanaWebhookPayload) -> IncidentAutopsyReport:
    try:
        alert = GrafanaAlertAdapter().to_alert_context(payload)
        packet = build_incident_evidence_provider(alert).load_evidence(alert)
        model = _incident_model(alert.model or packet.model)
        report = DevSentinelOrchestrator().run_incident_autopsy_packet(packet, model)
        _save_incident(alert, report, source="grafana")
        return report
    except GrafanaAlertAdapterError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IncidentEvidenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": exc.errors(),
            },
        ) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/incidents/evidence/test", response_model=EvidenceConnectionTestResult)
def test_incident_evidence_connection(config: IncidentEvidenceConfig | None = None) -> EvidenceConnectionTestResult:
    return EvidenceConnectionTester(evidence_config=config).test()


@router.post("/incidents/analyze", response_model=IncidentAutopsyReport)
def run_incident_packet_analysis(packet: IncidentEvidencePacket) -> IncidentAutopsyReport:
    try:
        report = DevSentinelOrchestrator().run_incident_autopsy_packet(packet, _incident_model(packet.model or packet.alert.model))
        _save_incident(packet.alert, report, source=packet.source_provider)
        return report
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model output failed schema validation",
                "errors": exc.errors(),
            },
        ) from exc
    except ModelOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ModelGatewayError as exc:
        raise _provider_error(exc) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
