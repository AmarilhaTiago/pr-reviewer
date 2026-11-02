"""Filter, split and deduplicate raw LLM findings."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from reviewer.diff import FileDiff
from reviewer.schema import Finding

_SEVERITY_RANK = {"blocker": 0, "major": 1, "minor": 2}


@dataclass
class PostResult:
    inline: list[Finding] = field(default_factory=list)
    low_confidence: list[Finding] = field(default_factory=list)
    dropped: int = 0


def _valid_lines(files: Iterable[FileDiff]) -> dict[str, set[int]]:
    return {
        f.path: {
            line.new_number for h in f.hunks for line in h.lines if line.new_number is not None
        }
        for f in files
    }


def _quality(f: Finding) -> tuple[int, float]:
    return (_SEVERITY_RANK[f.severity], -f.confidence)


def _dedupe(findings: list[Finding]) -> list[Finding]:
    kept: list[Finding] = []
    for f in sorted(findings, key=_quality):
        if not any(
            k.file == f.file and k.category == f.category and abs(k.line - f.line) <= 2
            for k in kept
        ):
            kept.append(f)
    return sorted(kept, key=lambda x: (_SEVERITY_RANK[x.severity], x.file, x.line))


def postprocess(
    findings: Iterable[Finding], files: Iterable[FileDiff], min_confidence: float = 0.5
) -> PostResult:
    valid = _valid_lines(files)
    result = PostResult()
    confident: list[Finding] = []
    unsure: list[Finding] = []
    for f in findings:
        if f.line not in valid.get(f.file, set()):
            result.dropped += 1
        elif f.confidence < min_confidence:
            unsure.append(f)
        else:
            confident.append(f)
    result.inline = _dedupe(confident)
    result.low_confidence = _dedupe(unsure)
    return result
