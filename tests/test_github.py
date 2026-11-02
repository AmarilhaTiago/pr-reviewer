import json

import httpx
import pytest

from reviewer.github import GitHubClient, GitHubError, publish
from reviewer.llm import Usage
from reviewer.pipeline import ReviewResult
from reviewer.schema import Finding
from reviewer.summary import MARKER, inline_body, render_summary, verdict


def finding(line=2, sev="major", file="a.py", title="Bad thing", conf=0.9) -> Finding:
    return Finding(
        file=file,
        line=line,
        severity=sev,
        category="bug",
        title=title,
        explanation="Because.",
        suggestion="Fix it.",
        confidence=conf,
    )


def result(*findings, **kw) -> ReviewResult:
    return ReviewResult(inline=list(findings), usage=Usage(100, 20, 2), **kw)


class FakeGitHub:
    """Tiny in-memory GitHub REST API."""

    def __init__(self, review_status=200, issue_comments=None, review_comments=None):
        self.requests: list[tuple[str, str, dict]] = []
        self.review_status = review_status
        self.issue_comments = issue_comments or []
        self.review_comments = review_comments or []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        self.requests.append((request.method, request.url.path, body))
        path, method = request.url.path, request.method
        if method == "GET" and path.endswith("/pulls/7"):
            return httpx.Response(
                200, text="DIFF TEXT", headers={"x-accept": request.headers["accept"]}
            )
        if method == "GET" and path.endswith("/pulls/7/comments"):
            page = int(request.url.params["page"])
            return httpx.Response(200, json=self.review_comments[(page - 1) * 100 : page * 100])
        if method == "GET" and path.endswith("/issues/7/comments"):
            return httpx.Response(200, json=self.issue_comments)
        if method == "POST" and path.endswith("/pulls/7/reviews"):
            return httpx.Response(self.review_status, json={})
        if method in ("POST", "PATCH") and "/issues/" in path:
            return httpx.Response(200 if method == "PATCH" else 201, json={"id": 1})
        return httpx.Response(404, json={"message": "nope"})

    def calls(self, method, suffix):
        return [b for m, p, b in self.requests if m == method and p.endswith(suffix)]


def client(fake: FakeGitHub) -> GitHubClient:
    return GitHubClient(
        "tok",
        "o/r",
        client=httpx.Client(transport=httpx.MockTransport(fake)),
        api_url="https://api.test",
    )


def test_review_has_inline_comments_with_right_side():  # AC1
    fake = FakeGitHub()
    out = publish(client(fake), 7, result(finding(2), finding(5, "minor")), "m", None)
    (review,) = fake.calls("POST", "/pulls/7/reviews")
    assert review["event"] == "COMMENT"
    assert [(c["path"], c["line"], c["side"]) for c in review["comments"]] == [
        ("a.py", 2, "RIGHT"),
        ("a.py", 5, "RIGHT"),
    ]
    assert out.posted == 2


def test_min_severity_filters_inline_comments():  # AC1
    fake = FakeGitHub()
    out = publish(
        client(fake), 7, result(finding(2, "major"), finding(5, "minor")), "m", None, "major"
    )
    (review,) = fake.calls("POST", "/pulls/7/reviews")
    assert len(review["comments"]) == 1 and out.hidden == 1


def test_summary_content():  # AC2
    text = render_summary(
        result(
            finding(2, "blocker"),
            finding(3, "minor"),
            ignored=["x.lock"],
            skipped=["big.py"],
            failed=["bad.py"],
            low_confidence=[finding(9, conf=0.3, title="Maybe")],
        ),
        "gemini-x",
        0.0123,
    )
    assert text.startswith(MARKER)
    assert "⛔" in text and "| ⛔ blocker | 1 |" in text and "| 💡 minor | 1 |" in text
    for fragment in ("x.lock", "big.py", "bad.py", "Maybe", "100 in / 20 out", "US$ 0.0123"):
        assert fragment in text
    assert verdict([]) == "✅ No blocking issues"
    assert verdict([finding(sev="major")]).startswith("⚠️")
    assert "n/a" in render_summary(result(), "m", None)


def test_summary_is_created_then_updated_never_duplicated():  # AC3
    fake = FakeGitHub()
    out = publish(client(fake), 7, result(finding()), "m", None)
    assert out.summary == "created" and len(fake.calls("POST", "/issues/7/comments")) == 1

    fake = FakeGitHub(
        issue_comments=[{"id": 55, "body": "unrelated"}, {"id": 99, "body": f"{MARKER}\nold"}]
    )
    out = publish(client(fake), 7, result(finding()), "m", None)
    assert out.summary == "updated"
    assert fake.calls("POST", "/issues/7/comments") == []
    assert [p for m, p, _ in fake.requests if m == "PATCH"] == ["/repos/o/r/issues/comments/99"]


def posted(f: Finding) -> dict:
    """A review comment as the GitHub API returns it."""
    return {"path": f.file, "line": f.line, "original_line": f.line, "body": inline_body(f)}


def test_already_posted_findings_are_not_reposted():  # AC4
    f_old, f_new = finding(2), finding(8, title="Another", sev="minor")
    fake = FakeGitHub(review_comments=[posted(f_old), {"path": "a.py", "line": 3, "body": "human"}])
    out = publish(client(fake), 7, result(f_old, f_new), "m", None)
    (review,) = fake.calls("POST", "/pulls/7/reviews")
    assert [c["line"] for c in review["comments"]] == [8]
    assert (out.posted, out.already_posted) == (1, 1)


def test_same_issue_with_reworded_title_or_shifted_line_is_not_reposted():  # AC4
    """Regression: the LLM rewords titles between runs and lines shift by a few lines."""
    before = finding(5, title="SQL Injection vulnerability")
    after = finding(7, title="SQL Injection vulnerability via string formatting")
    fake = FakeGitHub(review_comments=[posted(before)])
    out = publish(client(fake), 7, result(after), "m", None)
    assert fake.calls("POST", "/pulls/7/reviews") == [] and out.already_posted == 1


def test_other_category_or_distant_line_is_a_new_comment():  # AC4
    before = finding(5)
    fake = FakeGitHub(review_comments=[posted(before)])
    other_cat = Finding(**{**finding(5).model_dump(), "category": "security"})
    out = publish(client(fake), 7, result(other_cat, finding(9)), "m", None)
    assert out.posted == 2 and out.already_posted == 0


def test_comment_whose_line_moved_uses_original_line():  # AC4
    outdated = {**posted(finding(5)), "line": None}  # GitHub nulls `line` when the diff moved
    fake = FakeGitHub(review_comments=[outdated])
    out = publish(client(fake), 7, result(finding(6)), "m", None)
    assert out.already_posted == 1


def test_rejected_review_moves_findings_to_summary():  # AC5
    fake = FakeGitHub(review_status=422)
    out = publish(client(fake), 7, result(finding(2, title="Lost one")), "m", None)
    assert out.posted == 0 and len(out.unplaced) == 1
    (summary,) = fake.calls("POST", "/issues/7/comments")
    assert "could not be placed inline" in summary["body"] and "Lost one" in summary["body"]


def test_get_diff_uses_diff_media_type_and_errors_are_clear():  # AC6
    fake = FakeGitHub()
    seen = {}

    def spy(request):
        seen["accept"] = request.headers["accept"]
        return fake(request)

    gh = GitHubClient(
        "tok",
        "o/r",
        client=httpx.Client(transport=httpx.MockTransport(spy)),
        api_url="https://api.test",
    )
    assert gh.get_diff(7) == "DIFF TEXT" and seen["accept"] == "application/vnd.github.diff"
    with pytest.raises(GitHubError, match="404"):
        gh.get_diff(8)


def test_pagination_collects_all_pages():  # AC6
    comments = [posted(finding(i + 1)) for i in range(150)]
    fake = FakeGitHub(review_comments=comments)
    assert len(client(fake).existing_comments(7)) == 150
    assert len(fake.calls("GET", "/pulls/7/comments")) == 2
