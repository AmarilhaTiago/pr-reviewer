import json

import pytest
from typer.testing import CliRunner

from reviewer import cli
from reviewer.llm import Usage
from reviewer.schema import Finding, Review
from reviewer.summary import MARKER

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

    def complete_json(self, system, user, schema):
        self.usage.add(10, 5)
        finding = Finding(
            file="a.py",
            line=2,
            severity="major",
            category="bug",
            title="Suspicious",
            explanation="Because.",
            confidence=0.9,
        )
        return Review(findings=[finding], summary="s")


class FakeGitHub:
    instances: list["FakeGitHub"] = []

    def __init__(self, token, repo, **kw):
        self.repo, self.published = repo, None
        FakeGitHub.instances.append(self)

    def get_diff(self, pr):
        return DIFF


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_EVENT_PATH", "LLM_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_MODEL", "m")
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setattr(cli, "make_provider", lambda *a, **kw: FakeProvider())
    monkeypatch.setattr(cli, "GitHubClient", FakeGitHub)
    FakeGitHub.instances.clear()
    return monkeypatch


def test_dry_run_prints_summary_without_publishing(env):  # AC7
    env.setenv("GITHUB_TOKEN", "t")
    env.setattr(cli, "publish", lambda *a, **kw: pytest.fail("must not publish"))
    res = runner.invoke(cli.app, ["pr", "--number", "7", "--repo", "o/r", "--dry-run"])
    assert res.exit_code == 0, res.output
    assert MARKER in res.output and "Suspicious" not in res.output.split(MARKER)[0]
    assert "| ⚠️ major | 1 |" in res.output


def test_publishes_using_event_payload_and_env(env, tmp_path):  # AC7
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 42}}))
    env.setenv("GITHUB_TOKEN", "t")
    env.setenv("GITHUB_REPOSITORY", "o/r")
    env.setenv("GITHUB_EVENT_PATH", str(event))
    seen = {}

    def fake_publish(gh, number, result, model, cost, min_severity):
        seen.update(repo=gh.repo, number=number, severity=min_severity, n=len(result.inline))
        from reviewer.github import PublishOutcome

        return PublishOutcome(posted=1, summary="created")

    env.setattr(cli, "publish", fake_publish)
    res = runner.invoke(cli.app, ["pr", "--min-severity", "major"])
    assert res.exit_code == 0, res.output
    assert seen == {"repo": "o/r", "number": 42, "severity": "major", "n": 1}
    assert "posted 1 inline" in res.output and "summary created" in res.output


def test_missing_token_or_pr_number_is_a_clear_error(env):  # AC7
    res = runner.invoke(cli.app, ["pr", "--number", "7", "--repo", "o/r"])
    assert res.exit_code == 2 and "GITHUB_TOKEN" in res.output
