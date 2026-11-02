"""Command line interface."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from reviewer.config import Settings, load_dotenv
from reviewer.cost import estimate_cost
from reviewer.evals.report import render_table, write_results
from reviewer.evals.runner import load_cases, run_evals
from reviewer.llm import LLMProvider, make_provider
from reviewer.pipeline import review_diff
from reviewer.render import render_json, render_markdown

app = typer.Typer(help="LLM-powered pull request reviewer.", no_args_is_help=True)


class Format(StrEnum):
    md = "md"
    json = "json"


def fail(message: str) -> None:
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(2)


def read_diff(diff: Path | None, base: str | None) -> str:
    if (diff is None) == (base is None):
        fail("provide exactly one of --diff or --base")
    if diff is not None:
        if not diff.is_file():
            fail(f"diff file not found: {diff}")
        return diff.read_text(encoding="utf-8", errors="replace")
    proc = subprocess.run(
        ["git", "diff", f"{base}...HEAD"], capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        fail(f"git diff failed: {proc.stderr.strip()}")
    return proc.stdout


def setup_provider(model: str | None) -> tuple[Settings, LLMProvider]:
    try:
        cfg = Settings.from_env()
    except ValueError as exc:
        fail(f"invalid configuration: {exc}")
    if model:
        cfg = replace(cfg, model=model)
    if not cfg.model:
        fail("LLM_MODEL is not set")
    try:
        provider = make_provider(
            cfg.provider,
            cfg.model,
            cfg.api_key,
            cfg.base_url,
            min_interval=cfg.call_interval_seconds,
        )
    except ValueError as exc:
        fail(str(exc))
    return cfg, provider


@app.callback()
def main() -> None:
    pass


@app.command()
def evals(
    model: Annotated[str | None, typer.Option("--model", help="Override LLM_MODEL.")] = None,
    cases: Annotated[Path, typer.Option("--cases", help="Eval cases directory.")] = Path(
        "evals/cases"
    ),
    out: Annotated[Path, typer.Option("--out", help="Results directory.")] = Path("evals/results"),
    rules: Annotated[Path | None, typer.Option("--rules", help="Team rules.")] = Path(
        ".reviewer/rules.md"
    ),
) -> None:
    """Run the eval cases and print precision, recall, false positives, cost and latency."""
    load_dotenv()
    if not cases.is_dir():
        fail(f"cases directory not found: {cases}")
    rules_text = rules.read_text(encoding="utf-8") if rules and rules.is_file() else ""
    cfg, provider = setup_provider(model)
    report = run_evals(
        load_cases(cases),
        provider,
        cfg.model,
        rules=rules_text,
        ignore_patterns=list(cfg.ignore_globs),
        max_tokens_per_chunk=cfg.max_tokens_per_chunk,
        max_tokens_per_pr=cfg.max_tokens_per_pr,
        min_confidence=cfg.min_confidence,
    )
    path = write_results(report, out)
    typer.echo(render_table(report))
    typer.echo(f"\nResults written to {path}")


@app.command()
def review(
    diff: Annotated[Path | None, typer.Option("--diff", help="Path to a unified diff.")] = None,
    base: Annotated[str | None, typer.Option("--base", help="Git ref (REF...HEAD).")] = None,
    rules: Annotated[Path | None, typer.Option("--rules", help="Team rules (Markdown).")] = None,
    format: Annotated[Format, typer.Option("--format", help="Output format.")] = Format.md,
) -> None:
    """Review a diff and print the findings, tokens and cost."""
    load_dotenv()
    text = read_diff(diff, base)
    rules_text = ""
    if rules is not None:
        if not rules.is_file():
            fail(f"rules file not found: {rules}")
        rules_text = rules.read_text(encoding="utf-8")
    cfg, provider = setup_provider(None)
    result = review_diff(
        text,
        provider,
        rules=rules_text,
        ignore_patterns=list(cfg.ignore_globs),
        max_tokens_per_chunk=cfg.max_tokens_per_chunk,
        max_tokens_per_pr=cfg.max_tokens_per_pr,
        min_confidence=cfg.min_confidence,
    )
    cost = estimate_cost(cfg.model, result.usage)
    render = render_json if format is Format.json else render_markdown
    typer.echo(render(result, cfg.model, cost))


if __name__ == "__main__":
    app()
