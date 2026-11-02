"""Scoring of findings against expected findings."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from reviewer.schema import Finding


@dataclass(frozen=True)
class Expected:
    file: str
    line: int
    category: str


@dataclass(frozen=True)
class CaseScore:
    tp: int
    fp: int
    fn: int
    clean: bool  # the case has no expected findings


@dataclass(frozen=True)
class Metrics:
    precision: float | None
    recall: float | None
    false_positive_rate: float | None
    tp: int
    fp: int
    fn: int


def is_match(finding: Finding, expected: Expected, tolerance: int = 3) -> bool:
    return (
        finding.file == expected.file
        and finding.category == expected.category
        and abs(finding.line - expected.line) <= tolerance
    )


def score_case(findings: Sequence[Finding], expected: Sequence[Expected]) -> CaseScore:
    unmatched = list(findings)
    tp = 0
    for exp in expected:
        hit = next((f for f in unmatched if is_match(f, exp)), None)
        if hit is not None:
            unmatched.remove(hit)
            tp += 1
    return CaseScore(tp=tp, fp=len(unmatched), fn=len(expected) - tp, clean=not expected)


def _ratio(num: int, den: int) -> float | None:
    return num / den if den else None


def aggregate(scores: Iterable[CaseScore]) -> Metrics:
    scores = list(scores)
    tp, fp, fn = (sum(getattr(s, k) for s in scores) for k in ("tp", "fp", "fn"))
    clean = [s for s in scores if s.clean]
    return Metrics(
        precision=_ratio(tp, tp + fp),
        recall=_ratio(tp, tp + fn),
        false_positive_rate=_ratio(sum(1 for s in clean if s.fp > 0), len(clean)),
        tp=tp,
        fp=fp,
        fn=fn,
    )
