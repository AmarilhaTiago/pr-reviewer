import pytest
from typer.testing import CliRunner

from reviewer import cli
from reviewer.llm import Usage
from reviewer.schema import Review

runner = CliRunner()


class FakeProvider:
    def __init__(self):
        self.usage = Usage()

    def complete_json(self, system, user, schema):
        self.usage.add(1, 1)
        return Review(findings=[], summary="s")


@pytest.fixture
def seen(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "GROQ_API_KEY", "LLM_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-x")
    monkeypatch.setenv("LLM_API_KEY", "gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    cases = tmp_path / "cases" / "c"
    cases.mkdir(parents=True)
    (cases / "diff.patch").write_text("")
    (cases / "expected.json").write_text('{"expected": []}')
    calls: list[tuple] = []

    def fake_make(provider, model, key, base_url=None, **kw):
        calls.append((provider, model, key))
        return FakeProvider()

    monkeypatch.setattr(cli, "make_provider", fake_make)
    return calls


def run_evals(*args):
    return runner.invoke(cli.app, ["evals", "--cases", "cases", "--out", "out", *args])


def test_default_provider_uses_llm_api_key(seen):  # AC8
    assert run_evals().exit_code == 0
    assert seen == [("gemini", "gemini-x", "gemini-key")]


def test_provider_flag_uses_provider_specific_key(seen):  # AC8
    res = run_evals("--provider", "groq", "--model", "openai/gpt-oss-120b")
    assert res.exit_code == 0, res.output
    assert seen == [("groq", "openai/gpt-oss-120b", "groq-key")]


def test_provider_flag_without_its_key_is_a_clear_error(seen, monkeypatch):  # AC8
    monkeypatch.delenv("GROQ_API_KEY")
    res = run_evals("--provider", "groq", "--model", "m")
    assert res.exit_code == 2 and "GROQ_API_KEY" in res.output
    assert seen == []


def test_provider_flag_requires_explicit_model(seen):  # AC8
    res = run_evals("--provider", "groq")
    assert res.exit_code == 2 and "--model" in res.output


def test_evals_abort_without_writing_results_when_every_case_fails(seen, monkeypatch, tmp_path):
    from reviewer.llm import LLMError

    class Broken(FakeProvider):
        def complete_json(self, system, user, schema):
            raise LLMError("HTTP 401: Invalid API Key")

    monkeypatch.setattr(cli, "make_provider", lambda *a, **kw: Broken())
    (tmp_path / "cases" / "c" / "diff.patch").write_text(
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1,1 +1,2 @@\n x\n+y\n"
    )
    res = run_evals()
    assert res.exit_code == 2 and "every case failed" in res.output
    assert not (tmp_path / "out").exists()
