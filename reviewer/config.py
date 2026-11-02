"""Configuration from environment variables."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from reviewer.filtering import DEFAULT_IGNORE, parse_patterns


def load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader; never overrides variables already set."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    provider: str = "gemini"
    model: str = ""
    api_key: str = ""
    base_url: str | None = None
    max_tokens_per_chunk: int = 6000
    max_tokens_per_pr: int = 60000
    min_confidence: float = 0.5
    call_interval_seconds: float = 2.0
    ignore_globs: tuple[str, ...] = tuple(DEFAULT_IGNORE)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        globs = parse_patterns(env.get("IGNORE_GLOBS", "")) or list(DEFAULT_IGNORE)
        return cls(
            provider=env.get("LLM_PROVIDER", "gemini"),
            model=env.get("LLM_MODEL", ""),
            api_key=env.get("LLM_API_KEY", ""),
            base_url=env.get("LLM_BASE_URL") or None,
            max_tokens_per_chunk=int(env.get("MAX_TOKENS_PER_CHUNK", 6000)),
            max_tokens_per_pr=int(env.get("MAX_TOKENS_PER_PR", 60000)),
            min_confidence=float(env.get("MIN_CONFIDENCE", 0.5)),
            call_interval_seconds=float(env.get("CALL_INTERVAL_SECONDS", 2)),
            ignore_globs=tuple(globs),
        )
