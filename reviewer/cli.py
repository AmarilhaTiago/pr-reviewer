"""Command line interface."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from reviewer.config import Settings, load_dotenv
from reviewer.cost import estimate_cost
from reviewer.evals.report import render_table, write_results
from reviewer.evals.runner import load_cases, run_evals
from reviewer.github import GitHubClient, GitHubError, publish
from reviewer.llm import LLMProvider, make_provider
from reviewer.pipeline import review_diff
from reviewer.render import render_json, render_markdown
from reviewer.summary import render_summary

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


def _force_utf8_output() -> None:
    """Windows consoles default to cp1252, which cannot print the emoji in our reports."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


@app.callback()
def main() -> None:
    _force_utf8_output()


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


class MinSeverity(StrEnum):
    minor = "minor"
    major = "major"
    blocker = "blocker"


def pr_number_from_event() -> int | None:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not Path(path).is_file():
        return None
    event = json.loads(Path(path).read_text(encoding="utf-8"))
    number = (event.get("pull_request") or {}).get("number") or event.get("number")
    return int(number) if number else None


@app.command()
def pr(
    number: Annotated[int | None, typer.Option("--number", help="PR number.")] = None,
    repo: Annotated[str | None, typer.Option("--repo", help="owner/name.")] = None,
    rules: Annotated[Path | None, typer.Option("--rules", help="Team rules.")] = None,
    min_severity: Annotated[
        MinSeverity, typer.Option("--min-severity", help="Lowest severity to post.")
    ] = MinSeverity.minor,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print, do not post.")] = False,
) -> None:
    """Review a GitHub pull request and post inline comments plus a summary."""
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = repo or os.environ.get("GITHUB_REPOSITORY", "")
    number = number or pr_number_from_event()
    if not token or not repo or not number:
        fail("need GITHUB_TOKEN, a repository (--repo / GITHUB_REPOSITORY) and a PR number")
    rules_text = ""
    if rules is not None:
        if not rules.is_file():
            fail(f"rules file not found: {rules}")
        rules_text = rules.read_text(encoding="utf-8")
    cfg, provider = setup_provider(None)
    gh = GitHubClient(token, repo)
    try:
        diff_text = gh.get_diff(number)
        result = review_diff(
            diff_text,
            provider,
            rules=rules_text,
            ignore_patterns=list(cfg.ignore_globs),
            max_tokens_per_chunk=cfg.max_tokens_per_chunk,
            max_tokens_per_pr=cfg.max_tokens_per_pr,
            min_confidence=cfg.min_confidence,
        )
        cost = estimate_cost(cfg.model, result.usage)
        if dry_run:
            typer.echo(render_summary(result, cfg.model, cost))
            return
        outcome = publish(gh, number, result, cfg.model, cost, min_severity.value)
    except GitHubError as exc:
        fail(str(exc))
    typer.echo(
        f"posted {outcome.posted} inline comment(s), {outcome.already_posted} already present, "
        f"summary {outcome.summary}"
    )


if __name__ == "__main__":
    app()
