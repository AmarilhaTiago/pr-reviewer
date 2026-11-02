from reviewer.llm import LLMError, Usage
from reviewer.pipeline import review_diff
from reviewer.schema import Finding, Review

DIFF = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
 one
+two
 three
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1,1 +1,2 @@
 x
+y
diff --git a/poetry.lock b/poetry.lock
--- a/poetry.lock
+++ b/poetry.lock
@@ -1,1 +1,2 @@
 a
+b
"""


def finding(file: str, line: int, conf: float = 0.9) -> Finding:
    return Finding(
        file=file,
        line=line,
        severity="major",
        category="bug",
        title="t",
        explanation="e",
        confidence=conf,
    )


class FakeProvider:
    def __init__(self, handler):
        self.handler = handler
        self.usage = Usage()
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system, user, schema):
        self.calls.append((system, user))
        self.usage.add(10, 5)
        return self.handler(user)


def ok(user: str) -> Review:
    if "File: a.py" in user:
        return Review(findings=[finding("a.py", 2), finding("a.py", 99)], summary="sa")
    return Review(findings=[finding("b.py", 2, conf=0.2)], summary="sb")


def test_pipeline_end_to_end_with_fake_llm():  # AC3
    provider = FakeProvider(ok)
    res = review_diff(DIFF, provider, rules="- be nice")
    assert [(f.file, f.line) for f in res.inline] == [("a.py", 2)]
    assert [(f.file, f.line) for f in res.low_confidence] == [("b.py", 2)]
    assert res.dropped == 1
    assert res.ignored == ["poetry.lock"] and res.skipped == [] and res.failed == []
    assert sorted(res.summaries) == ["sa", "sb"]
    assert res.usage.calls == 2 and "- be nice" in provider.calls[0][0]


def test_llm_error_in_one_chunk_does_not_stop_others():  # AC4
    def handler(user):
        if "File: a.py" in user:
            raise LLMError("boom")
        return ok(user)

    res = review_diff(DIFF, FakeProvider(handler))
    assert res.failed == ["a.py"]
    assert [(f.file, f.line) for f in res.low_confidence] == [("b.py", 2)]


def test_empty_or_fully_ignored_diff_makes_no_calls():  # AC5
    provider = FakeProvider(ok)
    only_lock = DIFF[DIFF.index("diff --git a/poetry.lock") :]
    for text in ("", only_lock):
        res = review_diff(text, provider)
        assert res.inline == [] and res.usage.calls == 0
    assert provider.calls == []


def test_budget_skips_are_reported():  # AC3
    res = review_diff(DIFF, FakeProvider(ok), max_tokens_per_pr=1)
    assert sorted(res.skipped) == ["a.py", "b.py"]
