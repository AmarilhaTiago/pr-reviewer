import json
from datetime import date

import pytest
from typer.testing import CliRunner

from reviewer import cli
from reviewer.evals.metrics import CaseScore, Expected, aggregate, is_match, score_case
from reviewer.evals.report import render_table, write_results
from reviewer.evals.runner import load_cases, run_evals
from reviewer.llm import LLMError, Usage
from reviewer.schema import Finding, Review

DIFF = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
 one
+two
 three
"""


def finding(file="a.py", line=2, category="bug") -> Finding:
    return Finding(
        file=file,
        line=line,
        severity="major",
        category=category,
        title="t",
        explanation="e",
        confidence=0.9,
    )


def test_is_match_requires_file_category_and_line_within_3():  # AC1
    exp = Expected("a.py", 10, "bug")
    assert is_match(finding(line=13, file="a.py"), exp)
    assert not is_match(finding(line=14), exp)
    assert not is_match(finding(line=10, category="security"), exp)
    assert not is_match(finding(line=10, file="b.py"), exp)


def test_score_case_matches_one_to_one():  # AC1
    expected = [Expected("a.py", 2, "bug"), Expected("a.py", 3, "bug")]
    score = score_case([finding(line=2)], expected)
    assert (score.tp, score.fp, score.fn) == (1, 0, 1)
    score = score_case([finding(line=2), finding(line=2), finding(line=3)], expected)
    assert (score.tp, score.fp, score.fn) == (2, 1, 0)


def test_aggregate_metrics():  # AC2
    m = aggregate(
        [
            CaseScore(tp=2, fp=1, fn=1, clean=False),
            CaseScore(tp=0, fp=1, fn=0, clean=True),
            CaseScore(tp=0, fp=0, fn=0, clean=True),
        ]
    )
    assert m.precision == pytest.approx(2 / 4)
    assert m.recall == pytest.approx(2 / 3)
    assert m.false_positive_rate == pytest.approx(0.5)


def test_aggregate_undefined_values_are_none():  # AC2
    m = aggregate([CaseScore(tp=0, fp=0, fn=0, clean=False)])
    assert (m.precision, m.recall, m.false_positive_rate) == (None, None, None)


def write_case(root, name, expected, diff=DIFF):
    case = root / name
    case.mkdir()
    (case / "diff.patch").write_text(diff)
    (case / "expected.json").write_text(json.dumps({"expected": expected}))


def test_load_cases_sorted_and_validated(tmp_path):  # AC3
    write_case(tmp_path, "b-case", [])
    write_case(tmp_path, "a-case", [{"file": "a.py", "line": 2, "category": "bug"}])
    cases = load_cases(tmp_path)
    assert [c.name for c in cases] == ["a-case", "b-case"]
    assert cases[0].expected == [Expected("a.py", 2, "bug")]
    (tmp_path / "c-case").mkdir()
    (tmp_path / "c-case" / "diff.patch").write_text(DIFF)
    with pytest.raises(FileNotFoundError, match="expected.json"):
        load_cases(tmp_path)


class FakeProvider:
    def __init__(self, fail_on=None):
        self.usage = Usage()
        self.fail_on = fail_on

    def complete_json(self, system, user, schema):
        if self.fail_on and self.fail_on in user:
            raise LLMError("boom")
        self.usage.add(1000, 500)
        return Review(findings=[finding()], summary="s")


def test_runner_measures_latency_tokens_cost_and_errors(tmp_path):  # AC4
    write_case(tmp_path, "good", [{"file": "a.py", "line": 2, "category": "bug"}])
    write_case(tmp_path, "clean", [])
    ticks = iter([0.0, 2.0, 10.0, 11.0])
    report = run_evals(
        load_cases(tmp_path),
        FakeProvider(),
        "m",
        prices={"m": {"input": 1.0, "output": 2.0}},
        clock=lambda: next(ticks),
    )
    clean, good = report.results
    assert (clean.name, clean.latency_seconds, clean.score.fp) == ("clean", 2.0, 1)
    assert (good.latency_seconds, good.score.tp) == (1.0, 1)
    assert good.prompt_tokens == 1000 and good.cost_usd == pytest.approx(0.002)
    assert report.avg_latency == pytest.approx(1.5)

    failing = run_evals(load_cases(tmp_path), FakeProvider(fail_on="a.py"), "m")
    assert all(r.error for r in failing.results) and all(not r.findings for r in failing.results)


def test_results_file_and_table(tmp_path):  # AC5
    write_case(tmp_path, "good", [{"file": "a.py", "line": 2, "category": "bug"}])
    report = run_evals(
        load_cases(tmp_path),
        FakeProvider(),
        "org/model:1",
        prices={"org/model:1": {"input": 1, "output": 1}},
    )
    path = write_results(report, tmp_path.parent / (tmp_path.name + "-out"), date(2026, 11, 2))
    assert path.name == "2026-11-02-org-model-1.json"
    data = json.loads(path.read_text())
    assert data["metrics"]["precision"] == 1.0 and data["cases"][0]["name"] == "good"
    table = render_table(report)
    assert "| org/model:1 | 100% | 100% | n/a |" in table
    no_price = render_table(run_evals(load_cases(tmp_path), FakeProvider(), "x"))
    assert "n/a" in no_price


def test_cli_evals_command(tmp_path, monkeypatch):  # AC6
    cases = tmp_path / "cases"
    cases.mkdir()
    write_case(cases, "good", [{"file": "a.py", "line": 2, "category": "bug"}])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_MODEL", "env-model")
    monkeypatch.setenv("LLM_API_KEY", "k")
    seen = {}

    def fake_make(provider, model, key, base_url=None, **kw):
        seen["model"] = model
        return FakeProvider()

    monkeypatch.setattr(cli, "make_provider", fake_make)
    res = CliRunner().invoke(
        cli.app,
        ["evals", "--model", "cli-model", "--cases", str(cases), "--out", str(tmp_path / "res")],
    )
    assert res.exit_code == 0, res.output
    assert seen["model"] == "cli-model"
    assert "| cli-model |" in res.output
    assert list((tmp_path / "res").glob("*-cli-model.json"))
