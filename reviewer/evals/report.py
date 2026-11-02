"""Persist and render eval results."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from reviewer.evals.runner import EvalReport


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _usd(value: float | None) -> str:
    return "n/a" if value is None else f"US$ {value:.4f}"


def _secs(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}s"


def render_table(report: EvalReport) -> str:
    m = report.metrics
    return "\n".join(
        [
            "| Model | Precision | Recall | False-positive rate | Avg cost/case | Avg latency |",
            "|---|---|---|---|---|---|",
            f"| {report.model} | {_pct(m.precision)} | {_pct(m.recall)} | "
            f"{_pct(m.false_positive_rate)} | {_usd(report.avg_cost)} | "
            f"{_secs(report.avg_latency)} |",
        ]
    )


def write_results(report: EvalReport, out_dir: Path, day: date | None = None) -> Path:
    day = day or date.today()
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", report.model).strip("-")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{day.isoformat()}-{slug}.json"
    m = report.metrics
    payload = {
        "model": report.model,
        "date": day.isoformat(),
        "metrics": {
            "precision": m.precision,
            "recall": m.recall,
            "false_positive_rate": m.false_positive_rate,
            "tp": m.tp,
            "fp": m.fp,
            "fn": m.fn,
            "avg_cost_usd": report.avg_cost,
            "avg_latency_seconds": report.avg_latency,
        },
        "cases": [
            {
                "name": r.name,
                "tp": r.score.tp,
                "fp": r.score.fp,
                "fn": r.score.fn,
                "latency_seconds": r.latency_seconds,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "cost_usd": r.cost_usd,
                "error": r.error,
                "findings": [f.model_dump() for f in r.findings],
            }
            for r in report.results
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
