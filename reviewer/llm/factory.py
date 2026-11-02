"""Build a provider from configuration."""

from __future__ import annotations

from reviewer.llm.base import LLMProvider
from reviewer.llm.openai_compatible import OpenAICompatibleProvider

PRESETS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "groq": "https://api.groq.com/openai/v1",
}


def make_provider(
    provider: str, model: str, api_key: str, base_url: str | None = None, **kwargs
) -> LLMProvider:
    if not api_key:
        raise ValueError("LLM_API_KEY is empty")
    if provider in PRESETS:
        url = base_url or PRESETS[provider]
    elif provider == "openai-compatible":
        if not base_url:
            raise ValueError("provider 'openai-compatible' requires a base URL")
        url = base_url
    else:
        known = ", ".join([*PRESETS, "openai-compatible"])
        raise ValueError(f"unknown provider {provider!r} (known: {known})")
    return OpenAICompatibleProvider(url, api_key, model, **kwargs)
