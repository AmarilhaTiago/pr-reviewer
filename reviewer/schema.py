"""Structured output schema the LLM must produce."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["blocker", "major", "minor"]
Category = Literal["bug", "security", "performance", "readability", "convention"]


class Finding(BaseModel):
    file: str
    line: int = Field(ge=1, description="Line number in the NEW file")
    severity: Severity
    category: Category
    title: str = Field(max_length=80)
    explanation: str
    suggestion: str | None = None
    confidence: float = Field(ge=0, le=1)


class Review(BaseModel):
    findings: list[Finding]
    summary: str
