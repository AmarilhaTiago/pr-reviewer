"""Render a ReviewResult as Markdown or JSON."""

from __future__ import annotations

import json

from reviewer.pipeline import ReviewResult
from reviewer.schema import Finding

SEVERITIES = ("blocker", "major", "minor")
ICONS = {"blocker": "⛔", "major": "⚠️", "minor": "💡"}


def format_cost(cost: float | None) -> str:
    return "n/a" if cost is None else f"US$ {cost:.4f}"


def finding_md(f: Finding) -> str:
    text = f"- **{f.title}** (`{f.file}:{f.line}`, {f.category}, confidence {f.confidence:.2f})\n"
    text += f"  {f.explanation}"
    if f.suggestion:
        text += f"\n  Suggestion: {f.suggestion}"
    return text


def render_markdown(result: ReviewResult, model: str, cost: float | None) -> str:
    lines = [f"# PR review ({model})", ""]
    if not result.inline:
        lines += ["No findings above the confidence threshold.", ""]
    for sev in SEVERITIES:
        group = [f for f in result.inline if f.severity == sev]
        if group:
            lines += [f"## {ICONS[sev]} {sev.capitalize()} ({len(group)})", ""]
            lines += [finding_md(f) for f in group] + [""]
    if result.low_confidence:
        lines += [f"## Low confidence ({len(result.low_confidence)})", ""]
        lines += [finding_md(f) for f in result.low_confidence] + [""]
    for title, paths in (
        ("Ignored files", result.ignored),
        ("Skipped (token budget)", result.skipped),
        ("Failed (LLM error)", result.failed),
    ):
        if paths:
            lines += [f"**{title}:** " + ", ".join(f"`{p}`" for p in paths), ""]
    u = result.usage
    lines.append(
        f"Tokens: {u.prompt_tokens} in / {u.completion_tokens} out "
        f"({u.calls} calls) · Cost: {format_cost(cost)}"
    )
    return "\n".join(lines)


def render_json(result: ReviewResult, model: str, cost: float | None) -> str:
    u = result.usage
    return json.dumps(
        {
            "model": model,
            "findings": [f.model_dump() for f in result.inline],
            "low_confidence": [f.model_dump() for f in result.low_confidence],
            "dropped": result.dropped,
            "ignored": result.ignored,
            "skipped": result.skipped,
            "failed": result.failed,
            "summaries": result.summaries,
            "usage": {
                "prompt_tokens": u.prompt_tokens,
                "completion_tokens": u.completion_tokens,
                "calls": u.calls,
            },
            "cost_usd": cost,
        },
        indent=2,
        ensure_ascii=False,
    )
