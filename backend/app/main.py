from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat as chat_endpoint
from app.api.routes import health as health_endpoint
from app.api.routes import list_models as list_models_endpoint
from app.api.routes import router
from app.schemas.chat import ChatRequest, ChatResponse, ModelInfo


app = FastAPI(
    title="DevSentinel API",
    description="AI-native engineering intelligence for PR review and incident autopsy.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return health_endpoint()


@app.get("/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    return await list_models_endpoint()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await chat_endpoint(request)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "DevSentinel", "status": "ok"}
