from reviewer.diff import parse_diff
from reviewer.postprocess import postprocess
from reviewer.schema import Finding

DIFF = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,3 +1,5 @@
 one
+two
+three
 four
 five
"""
FILES = parse_diff(DIFF)


def f(line=2, file="a.py", sev="major", cat="bug", conf=0.9) -> Finding:
    return Finding(
        file=file,
        line=line,
        severity=sev,
        category=cat,
        title="t",
        explanation="e",
        confidence=conf,
    )


def test_findings_outside_diff_are_dropped():  # AC1
    res = postprocess([f(line=2), f(line=99), f(file="other.py")], FILES)
    assert [x.line for x in res.inline] == [2]
    assert res.dropped == 2


def test_context_lines_are_valid():  # AC1
    assert len(postprocess([f(line=1)], FILES).inline) == 1


def test_low_confidence_goes_to_summary_only():  # AC2
    res = postprocess([f(conf=0.49), f(line=5, conf=0.5)], FILES)
    assert [x.line for x in res.low_confidence] == [2]
    assert [x.line for x in res.inline] == [5]


def test_duplicates_keep_highest_severity_then_confidence():  # AC3
    res = postprocess(
        [f(line=2, sev="minor"), f(line=3, sev="blocker"), f(line=4, sev="major", conf=0.99)], FILES
    )
    assert [(x.line, x.severity) for x in res.inline] == [(3, "blocker")]


def test_different_category_or_distance_not_duplicate():  # AC3
    res = postprocess([f(line=1), f(line=4), f(line=2, cat="security")], FILES)
    assert len(res.inline) == 3


def test_sorted_by_severity_file_line():  # AC4
    res = postprocess(
        [f(line=5, sev="minor", cat="bug"), f(line=1, sev="blocker", cat="security")], FILES
    )
    assert [x.severity for x in res.inline] == ["blocker", "minor"]
