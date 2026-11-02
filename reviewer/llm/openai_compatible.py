"""Provider for any OpenAI-compatible ``/chat/completions`` endpoint (Gemini, Groq, ...)."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable

import httpx
from pydantic import ValidationError

from reviewer.llm.base import LLMError, LLMProvider, T, Usage

log = logging.getLogger("reviewer.llm")

MAX_RATE_LIMIT_WAIT = 60.0
DEFAULT_RATE_LIMIT_WAIT = 5.0


def _extract_json(text: str) -> str:
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end > start else text


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        client: httpx.Client | None = None,
        min_interval: float = 0.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.usage = Usage()
        self.request_seconds = 0.0  # time spent in HTTP calls, excluding throttle waits
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=timeout)
        self._min_interval = min_interval
        self._sleep = sleep
        self._clock = clock
        self._last_call: float | None = None
        self._format = "json_schema"

    # -- public -----------------------------------------------------------------
    def complete_json(self, system: str, user: str, schema: type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        messages = [
            {
                "role": "system",
                "content": f"{system}\n\nRespond with a single JSON object that matches this "
                f"JSON schema, and nothing else:\n{schema_json}",
            },
            {"role": "user", "content": user},
        ]
        for attempt in (1, 2):
            text = self._chat(messages, schema)
            try:
                return schema.model_validate_json(_extract_json(text))
            except (ValidationError, ValueError) as exc:
                log.warning("invalid structured output (attempt %d): %s", attempt, exc)
                if attempt == 2:
                    raise LLMError(f"invalid structured output after retry: {exc}") from exc
                messages += [
                    {"role": "assistant", "content": text},
                    {
                        "role": "user",
                        "content": f"Your previous reply failed validation: {exc}\n"
                        "Return only the corrected JSON object.",
                    },
                ]
        raise AssertionError("unreachable")

    # -- internals --------------------------------------------------------------
    def _response_format(self, schema: type[T]) -> dict:
        if self._format == "json_schema":
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": False,
                },
            }
        return {"type": "json_object"}

    def _throttle(self) -> None:
        if self._last_call is not None and self._min_interval > 0:
            wait = self._min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def _post(self, messages: list[dict], schema: type[T]) -> httpx.Response:
        self._throttle()
        started = self._clock()
        try:
            return self._client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "response_format": self._response_format(schema),
                },
            )
        except httpx.HTTPError as exc:
            raise LLMError(f"network error: {exc}") from exc
        finally:
            self.request_seconds += self._clock() - started

    def _chat(self, messages: list[dict], schema: type[T]) -> str:
        resp = self._post(messages, schema)
        if resp.status_code == 400 and self._format == "json_schema":
            log.warning("json_schema rejected (%s); falling back to json_object", resp.text[:200])
            self._format = "json_object"
            resp = self._post(messages, schema)
        if resp.status_code == 429:
            try:
                wait = min(float(resp.headers.get("retry-after", "")), MAX_RATE_LIMIT_WAIT)
            except ValueError:
                wait = DEFAULT_RATE_LIMIT_WAIT
            log.warning("rate limited; waiting %.1fs", wait)
            self._sleep(wait)
            resp = self._post(messages, schema)
        if resp.status_code >= 400:
            raise LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        usage = data.get("usage") or {}
        self.usage.add(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        log.info(
            "llm call model=%s prompt=%s completion=%s",
            self.model,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"unexpected response shape: {exc}") from exc
