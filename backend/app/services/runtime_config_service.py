from __future__ import annotations

import json
import logging
from pathlib import Path

from app.schemas.runtime_config import RuntimeConfig, RuntimeRoute

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[2] / "runtime_config.json"


class RuntimeConfigService:
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config_path = config_path

    def load(self) -> RuntimeConfig:
        if not self.config_path.exists():
            return RuntimeConfig()

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.error(
                "runtime_config_invalid_json",
                extra={"path": str(self.config_path)},
            )
            return RuntimeConfig()

        return RuntimeConfig.model_validate(data)

    def save(self, config: RuntimeConfig) -> RuntimeConfig:
        self.config_path.write_text(
            json.dumps(config.model_dump(), indent=2),
            encoding="utf-8",
        )
        logger.info(
            "runtime_config_saved",
            extra={
                "path": str(self.config_path),
                "routes": sorted(config.task_routing.keys()),
            },
        )
        return config

    def get_route(self, task: str) -> RuntimeRoute | None:
        return self.load().task_routing.get(task)

    def get_model_gateway_config(self):
        return self.load().model_gateway
