"""Run the eval cases against a provider."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from reviewer.cost import estimate_cost
from reviewer.evals.metrics import CaseScore, Expected, Metrics, aggregate, score_case
from reviewer.llm import LLMError, LLMProvider, Usage
from reviewer.pipeline import review_diff
from reviewer.schema import Finding


@dataclass
class Case:
    name: str
    diff: str
    expected: list[Expected]


@dataclass
class CaseResult:
    name: str
    score: CaseScore
    findings: list[Finding]
    latency_seconds: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None
    error: str | None = None


@dataclass
class EvalReport:
    model: str
    results: list[CaseResult] = field(default_factory=list)

    @property
    def metrics(self) -> Metrics:
        return aggregate(r.score for r in self.results)

    @property
    def avg_latency(self) -> float | None:
        if not self.results:
            return None
        return sum(r.latency_seconds for r in self.results) / len(self.results)

    @property
    def avg_cost(self) -> float | None:
        costs = [r.cost_usd for r in self.results]
        if not costs or any(c is None for c in costs):
            return None
        return sum(costs) / len(costs)


def load_cases(directory: Path) -> list[Case]:
    cases: list[Case] = []
    for case_dir in sorted(p for p in directory.iterdir() if p.is_dir()):
        diff_file, expected_file = case_dir / "diff.patch", case_dir / "expected.json"
        for required in (diff_file, expected_file):
            if not required.is_file():
                raise FileNotFoundError(f"eval case {case_dir.name!r} is missing {required.name}")
        raw = json.loads(expected_file.read_text(encoding="utf-8"))
        cases.append(
            Case(
                name=case_dir.name,
                diff=diff_file.read_text(encoding="utf-8"),
                expected=[Expected(**e) for e in raw["expected"]],
            )
        )
    return cases


def run_evals(
    cases: list[Case],
    provider: LLMProvider,
    model: str,
    *,
    rules: str = "",
    prices: dict[str, dict[str, float]] | None = None,
    clock: Callable[[], float] = time.monotonic,
    **pipeline_kwargs,
) -> EvalReport:
    report = EvalReport(model=model)
    for case in cases:
        before = Usage(
            provider.usage.prompt_tokens, provider.usage.completion_tokens, provider.usage.calls
        )
        start = clock()
        error = None
        findings: list[Finding] = []
        try:
            result = review_diff(case.diff, provider, rules=rules, **pipeline_kwargs)
            findings = result.inline
            if result.failed:
                error = f"LLM failed for: {', '.join(result.failed)}"
        except LLMError as exc:  # pragma: no cover - the pipeline already absorbs LLMError
            error = str(exc)
        latency = clock() - start
        used = Usage(
            provider.usage.prompt_tokens - before.prompt_tokens,
            provider.usage.completion_tokens - before.completion_tokens,
            provider.usage.calls - before.calls,
        )
        report.results.append(
            CaseResult(
                name=case.name,
                score=score_case(findings, case.expected),
                findings=findings,
                latency_seconds=latency,
                prompt_tokens=used.prompt_tokens,
                completion_tokens=used.completion_tokens,
                cost_usd=estimate_cost(model, used, prices),
                error=error,
            )
        )
    return report
