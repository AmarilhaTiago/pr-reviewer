"""Minimal GitHub REST client: fetch a PR diff, post a review, upsert the summary."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from reviewer.pipeline import ReviewResult
from reviewer.schema import Finding
from reviewer.summary import MARKER, extract_fingerprints, fingerprint, inline_body, render_summary

SEVERITY_ORDER = {"minor": 0, "major": 1, "blocker": 2}


class GitHubError(Exception):
    pass


class GitHubClient:
    def __init__(
        self,
        token: str,
        repo: str,
        *,
        client: httpx.Client | None = None,
        api_url: str = "https://api.github.com",
    ) -> None:
        self.repo = repo
        self._api = api_url.rstrip("/")
        self._client = client or httpx.Client(timeout=60.0)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(
        self, method: str, path: str, *, accept: str = "application/vnd.github+json", **kw
    ):
        try:
            resp = self._client.request(
                method,
                f"{self._api}{path}",
                headers={**self._headers, "Accept": accept},
                **kw,
            )
        except httpx.HTTPError as exc:
            raise GitHubError(f"network error: {exc}") from exc
        return resp

    def _ok(self, resp: httpx.Response):
        if resp.status_code >= 400:
            raise GitHubError(f"GitHub API {resp.status_code}: {resp.text[:200]}")
        return resp

    def _paged(self, path: str) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            resp = self._ok(self._request("GET", path, params={"per_page": 100, "page": page}))
            batch = resp.json()
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1

    def get_diff(self, pr: int) -> str:
        resp = self._ok(
            self._request(
                "GET", f"/repos/{self.repo}/pulls/{pr}", accept="application/vnd.github.diff"
            )
        )
        return resp.text

    def existing_fingerprints(self, pr: int) -> set[str]:
        found: set[str] = set()
        for comment in self._paged(f"/repos/{self.repo}/pulls/{pr}/comments"):
            found |= extract_fingerprints(comment.get("body") or "")
        return found

    def post_review(self, pr: int, comments: list[dict]) -> bool:
        """Post inline comments as one review. Returns False if GitHub rejects them (422)."""
        resp = self._request(
            "POST",
            f"/repos/{self.repo}/pulls/{pr}/reviews",
            json={
                "event": "COMMENT",
                "body": "Automated first-pass review. See the summary comment.",
                "comments": comments,
            },
        )
        if resp.status_code == 422:
            return False
        self._ok(resp)
        return True

    def upsert_summary(self, pr: int, body: str) -> str:
        path = f"/repos/{self.repo}/issues/{pr}/comments"
        existing = next((c for c in self._paged(path) if MARKER in (c.get("body") or "")), None)
        if existing:
            self._ok(
                self._request(
                    "PATCH",
                    f"/repos/{self.repo}/issues/comments/{existing['id']}",
                    json={"body": body},
                )
            )
            return "updated"
        self._ok(self._request("POST", path, json={"body": body}))
        return "created"


@dataclass
class PublishOutcome:
    posted: int = 0
    already_posted: int = 0
    hidden: int = 0
    unplaced: list[Finding] = field(default_factory=list)
    summary: str = ""


def publish(
    gh: GitHubClient,
    pr: int,
    result: ReviewResult,
    model: str,
    cost: float | None,
    min_severity: str = "minor",
) -> PublishOutcome:
    outcome = PublishOutcome()
    threshold = SEVERITY_ORDER[min_severity]
    eligible = [f for f in result.inline if SEVERITY_ORDER[f.severity] >= threshold]
    outcome.hidden = len(result.inline) - len(eligible)

    known = gh.existing_fingerprints(pr)
    fresh = [f for f in eligible if fingerprint(f) not in known]
    outcome.already_posted = len(eligible) - len(fresh)

    if fresh:
        comments = [
            {"path": f.file, "line": f.line, "side": "RIGHT", "body": inline_body(f)} for f in fresh
        ]
        if gh.post_review(pr, comments):
            outcome.posted = len(fresh)
        else:
            outcome.unplaced = fresh

    visible = ReviewResult(**{**result.__dict__, "inline": eligible})
    body = render_summary(visible, model, cost, hidden=outcome.hidden, unplaced=outcome.unplaced)
    outcome.summary = gh.upsert_summary(pr, body)
    return outcome
