import json
import subprocess

import pytest
from typer.testing import CliRunner

from reviewer import cli
from reviewer.config import Settings
from reviewer.llm import Usage
from reviewer.schema import Finding, Review

DIFF = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
 one
+two
 three
"""

runner = CliRunner()


class FakeProvider:
    def __init__(self):
        self.usage = Usage()
        self.systems: list[str] = []

    def complete_json(self, system, user, schema):
        self.systems.append(system)
        self.usage.add(100, 20)
        finding = Finding(
            file="a.py",
            line=2,
            severity="major",
            category="bug",
            title="Suspicious line",
            explanation="Because.",
            confidence=0.9,
        )
        return Review(findings=[finding], summary="s")


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL", "IGNORE_GLOBS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "k")
    provider = FakeProvider()
    monkeypatch.setattr(cli, "make_provider", lambda *a, **kw: provider)
    (tmp_path / "x.diff").write_text(DIFF)
    return provider


def test_review_diff_prints_findings_tokens_and_cost(env):  # AC1
    res = runner.invoke(cli.app, ["review", "--diff", "x.diff"])
    assert res.exit_code == 0, res.output
    assert "Major (1)" in res.output and "Suspicious line" in res.output
    assert "100 in / 20 out" in res.output and "Cost: n/a" in res.output


def test_base_uses_git_diff(env, monkeypatch):  # AC2
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout=DIFF, stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    res = runner.invoke(cli.app, ["review", "--base", "main"])
    assert res.exit_code == 0 and seen["cmd"] == ["git", "diff", "main...HEAD"]


def test_git_failure_is_a_clear_error(env, monkeypatch):  # AC2
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 128, stdout="", stderr="bad ref"),
    )
    res = runner.invoke(cli.app, ["review", "--base", "nope"])
    assert res.exit_code == 2 and "bad ref" in res.output


def test_json_format_is_valid_json(env):  # AC3
    res = runner.invoke(cli.app, ["review", "--diff", "x.diff", "--format", "json"])
    data = json.loads(res.output)
    assert data["findings"][0]["title"] == "Suspicious line"
    assert data["usage"]["calls"] == 1 and data["cost_usd"] is None
    for key in ("low_confidence", "ignored", "skipped", "failed"):
        assert key in data


def test_rules_file_is_passed_to_prompt(env, tmp_path):  # AC4
    (tmp_path / "rules.md").write_text("- use strict types")
    res = runner.invoke(cli.app, ["review", "--diff", "x.diff", "--rules", "rules.md"])
    assert res.exit_code == 0 and "- use strict types" in env.systems[0]


def test_missing_rules_file_is_an_error(env):  # AC4
    res = runner.invoke(cli.app, ["review", "--diff", "x.diff", "--rules", "nope.md"])
    assert res.exit_code == 2 and "rules file not found" in res.output


def test_usage_errors(env):  # AC5
    assert runner.invoke(cli.app, ["review"]).exit_code == 2
    both = runner.invoke(cli.app, ["review", "--diff", "x.diff", "--base", "main"])
    assert both.exit_code == 2


def test_missing_model_or_key_is_a_clear_error(env, monkeypatch):  # AC5
    monkeypatch.delenv("LLM_MODEL")
    res = runner.invoke(cli.app, ["review", "--diff", "x.diff"])
    assert res.exit_code == 2 and "LLM_MODEL" in res.output and "Traceback" not in res.output


def test_settings_defaults_and_parsing():  # AC6
    s = Settings.from_env({})
    assert (s.provider, s.max_tokens_per_chunk, s.min_confidence) == ("gemini", 6000, 0.5)
    assert s.call_interval_seconds == 2 and "*.lock" in s.ignore_globs
    s = Settings.from_env(
        {"MAX_TOKENS_PER_CHUNK": "100", "MIN_CONFIDENCE": "0.7", "IGNORE_GLOBS": "a/**, b"}
    )
    assert (s.max_tokens_per_chunk, s.min_confidence) == (100, 0.7)
    assert s.ignore_globs == ("a/**", "b")
