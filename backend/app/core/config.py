from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    model_provider: Literal["demo", "openai_compatible", "ollama"] = Field(default="demo", alias="MODEL_PROVIDER")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1", alias="OLLAMA_MODEL")

    skill_path: str = Field(default="artifacts/SKILL.md", alias="SKILL_PATH")
    request_timeout_seconds: float = Field(default=60.0, alias="REQUEST_TIMEOUT_SECONDS", gt=0)
    default_temperature: float = Field(default=0.0, alias="DEFAULT_TEMPERATURE", ge=0.0, le=2.0)
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    github_api_base_url: str = Field(default="https://api.github.com", alias="GITHUB_API_BASE_URL")
    github_webhook_secret: Optional[str] = Field(default=None, alias="GITHUB_WEBHOOK_SECRET")
    github_webhook_default_model: Optional[str] = Field(default=None, alias="GITHUB_WEBHOOK_DEFAULT_MODEL")
    incident_evidence_provider: Literal["fixture", "local_file", "datadog", "loki_prometheus"] = Field(default="fixture", alias="INCIDENT_EVIDENCE_PROVIDER")
    incident_log_file_path: str = Field(default="app/log_sources/dashboard-api.log", alias="INCIDENT_LOG_FILE_PATH")
    incident_log_limit: int = Field(default=200, alias="INCIDENT_LOG_LIMIT", ge=1, le=1000)
    datadog_api_key: Optional[str] = Field(default=None, alias="DATADOG_API_KEY")
    datadog_app_key: Optional[str] = Field(default=None, alias="DATADOG_APP_KEY")
    datadog_site: str = Field(default="datadoghq.com", alias="DATADOG_SITE")
    loki_base_url: Optional[str] = Field(default=None, alias="LOKI_BASE_URL")
    prometheus_base_url: Optional[str] = Field(default=None, alias="PROMETHEUS_BASE_URL")
    notification_provider: Literal["none", "telegram", "slack", "webhook"] = Field(default="none", alias="NOTIFICATION_PROVIDER")
    notification_webhook_url: Optional[str] = Field(default=None, alias="NOTIFICATION_WEBHOOK_URL")
    telegram_bot_token: Optional[str] = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, alias="TELEGRAM_CHAT_ID")
    slack_webhook_url: Optional[str] = Field(default=None, alias="SLACK_WEBHOOK_URL")
    devsentinel_public_url: str = Field(default="http://localhost:3000", alias="DEVSENTINEL_PUBLIC_URL")

    @field_validator("model_provider", mode="before")
    @classmethod
    def normalize_model_provider(cls, value: str) -> str:
        if value == "openai":
            return "openai_compatible"
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def default_review_model(settings: Settings) -> str:
    if settings.github_webhook_default_model:
        return settings.github_webhook_default_model
    if settings.model_provider == "ollama":
        return settings.ollama_model
    if settings.model_provider == "openai_compatible":
        return settings.openai_model
    return "devsentinel-deterministic-demo"
