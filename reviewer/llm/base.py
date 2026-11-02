"""Provider-independent LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The provider could not produce a valid structured answer."""


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 0

    def add(self, prompt: int, completion: int) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.calls += 1


class LLMProvider(ABC):
    usage: Usage

    @abstractmethod
    def complete_json(self, system: str, user: str, schema: type[T]) -> T:
        """Return an instance of ``schema`` or raise :class:`LLMError`."""
