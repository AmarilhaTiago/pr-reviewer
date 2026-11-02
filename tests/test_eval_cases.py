from pathlib import Path

from reviewer.diff import parse_diff
from reviewer.evals.runner import load_cases

CASES_DIR = Path(__file__).parent.parent / "evals" / "cases"
CASES = load_cases(CASES_DIR)


def test_case_mix():  # AC1
    clean = [c for c in CASES if not c.expected]
    assert 15 <= len(CASES) <= 20
    assert 3 <= len(clean) <= 4
    php = [c for c in CASES if c.name.startswith("php-")]
    py = [c for c in CASES if c.name.startswith("py-")]
    assert len(php) + len(py) == len(CASES) and len(php) >= 6 and len(py) >= 6


def test_categories_cover_the_planned_kinds():  # AC1
    categories = {e.category for c in CASES for e in c.expected}
    assert {"security", "bug", "performance", "convention"} <= categories


def test_expected_lines_point_at_added_lines_of_the_right_file():  # AC2
    for case in CASES:
        added = {f.path: f.added_lines for f in parse_diff(case.diff)}
        for exp in case.expected:
            assert exp.line in added[exp.file], case.name


def test_every_case_has_a_readme():  # AC1
    for case in CASES:
        assert (CASES_DIR / case.name / "README.md").is_file(), case.name
