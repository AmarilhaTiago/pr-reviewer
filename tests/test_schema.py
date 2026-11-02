import pytest
from pydantic import ValidationError

from reviewer.schema import Finding, Review

VALID = {
    "file": "a.py",
    "line": 3,
    "severity": "major",
    "category": "bug",
    "title": "Off by one",
    "explanation": "Loop skips the last item.",
    "confidence": 0.8,
}


def test_valid_review_parses_with_optional_suggestion():  # AC1
    payload = Review(findings=[Finding(**VALID)], summary="ok").model_dump_json()
    review = Review.model_validate_json(payload)
    assert review.findings[0].suggestion is None
    assert review.findings[0].line == 3


@pytest.mark.parametrize(
    "change",
    [
        {"severity": "critical"},
        {"category": "style"},
        {"title": "x" * 81},
        {"confidence": 1.5},
        {"confidence": -0.1},
        {"line": 0},
    ],
)
def test_invalid_finding_rejected(change):  # AC2
    with pytest.raises(ValidationError):
        Finding(**{**VALID, **change})


def test_summary_is_required():  # AC3
    with pytest.raises(ValidationError):
        Review.model_validate({"findings": []})
