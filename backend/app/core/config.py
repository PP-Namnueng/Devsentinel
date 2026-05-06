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

    @field_validator("model_provider", mode="before")
    @classmethod
    def normalize_model_provider(cls, value: str) -> str:
        if value == "openai":
            return "openai_compatible"
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
