from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.config import get_settings


DEFAULT_SKILL_MEMORY = """# DevSentinel Engineering Memory

- Prefer deterministic and explainable behavior.
- Do not invent missing implementation details.
- Keep recommendations scoped, evidence-based, and practical.
"""


class SkillMemory:
    def __init__(self, default_path: Optional[str] = None) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        configured_path = default_path or get_settings().skill_path
        self.default_path = Path(configured_path)
        if not self.default_path.is_absolute():
            self.default_path = repo_root / self.default_path

    def load(self, requested_path: Optional[str] = None) -> str:
        path = Path(requested_path) if requested_path else self.default_path
        if not path.is_absolute():
            repo_root = Path(__file__).resolve().parents[3]
            path = repo_root / path
        if not path.exists():
            return DEFAULT_SKILL_MEMORY
        content = path.read_text(encoding="utf-8").strip()
        return content or DEFAULT_SKILL_MEMORY
