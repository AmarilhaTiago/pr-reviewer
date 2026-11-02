"""Text posted to the pull request: inline comment bodies and the summary."""

from __future__ import annotations

import re
from collections.abc import Sequence

from reviewer.pipeline import ReviewResult
from reviewer.render import ICONS, SEVERITIES, format_cost
from reviewer.schema import Finding

MARKER = "<!-- pr-reviewer -->"
_CATEGORY_MARKER = re.compile(r"<!-- pr-reviewer:category=([a-z]+) -->")


def inline_body(f: Finding) -> str:
    """Comment text. The hidden marker lets later runs recognise it by category + location,
    never by title: the LLM rewords titles between runs."""
    text = f"**{ICONS[f.severity]} {f.severity} · {f.category}** — {f.title}\n\n{f.explanation}"
    if f.suggestion:
        text += f"\n\n**Suggestion:** {f.suggestion}"
    return f"{text}\n\n<!-- pr-reviewer:category={f.category} -->"


def extract_category(body: str) -> str | None:
    match = _CATEGORY_MARKER.search(body)
    return match.group(1) if match else None


def verdict(findings: Sequence[Finding]) -> str:
    if any(f.severity == "blocker" for f in findings):
        return "⛔ Blocking issues found"
    if findings:
        return "⚠️ Review suggested"
    return "✅ No blocking issues"


def render_summary(
    result: ReviewResult,
    model: str,
    cost: float | None,
    *,
    hidden: int = 0,
    unplaced: Sequence[Finding] = (),
) -> str:
    shown = [*result.inline]
    lines = [MARKER, "## 🤖 pr-reviewer", "", f"**{verdict(shown)}**", ""]
    lines += ["| Severity | Findings |", "|---|---|"]
    for sev in SEVERITIES:
        lines.append(f"| {ICONS[sev]} {sev} | {sum(1 for f in shown if f.severity == sev)} |")
    if hidden:
        lines += ["", f"_{hidden} finding(s) below the minimum severity were not posted._"]
    if unplaced:
        lines += ["", "### Findings that could not be placed inline", ""]
        lines += [
            f"- `{f.file}:{f.line}` **{f.title}** ({f.severity}): {f.explanation}" for f in unplaced
        ]
    if result.low_confidence:
        lines += [
            "",
            f"<details><summary>Low confidence ({len(result.low_confidence)})</summary>",
            "",
        ]
        lines += [
            f"- `{f.file}:{f.line}` {f.title} ({f.confidence:.2f})" for f in result.low_confidence
        ]
        lines += ["", "</details>"]
    for title, paths in (
        ("Ignored files", result.ignored),
        ("Not reviewed (token budget)", result.skipped),
        ("Failed (LLM error)", result.failed),
    ):
        if paths:
            lines += ["", f"**{title}:** " + ", ".join(f"`{p}`" for p in paths)]
    u = result.usage
    lines += [
        "",
        f"<sub>{model} · {u.prompt_tokens} in / {u.completion_tokens} out tokens "
        f"({u.calls} calls) · cost {format_cost(cost)}</sub>",
    ]
    return "\n".join(lines)
