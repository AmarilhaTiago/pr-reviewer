"""Diff in, post-processed findings out."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from reviewer.chunking import build_chunks
from reviewer.diff import parse_diff
from reviewer.filtering import DEFAULT_IGNORE, filter_files
from reviewer.llm import LLMError, LLMProvider, Usage
from reviewer.postprocess import postprocess
from reviewer.prompt import build_system, build_user
from reviewer.schema import Finding, Review

log = logging.getLogger("reviewer.pipeline")


@dataclass
class ReviewResult:
    inline: list[Finding] = field(default_factory=list)
    low_confidence: list[Finding] = field(default_factory=list)
    dropped: int = 0
    ignored: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


def review_diff(
    diff_text: str,
    provider: LLMProvider,
    *,
    rules: str = "",
    ignore_patterns: list[str] | None = None,
    max_tokens_per_chunk: int = 6000,
    max_tokens_per_pr: int = 60000,
    min_confidence: float = 0.5,
) -> ReviewResult:
    patterns = DEFAULT_IGNORE if ignore_patterns is None else ignore_patterns
    kept, ignored = filter_files(parse_diff(diff_text), patterns)
    plan = build_chunks(kept, max_tokens_per_chunk, max_tokens_per_pr)
    result = ReviewResult(ignored=[f.path for f in ignored], skipped=plan.skipped)

    system = build_system(rules)
    raw: list[Finding] = []
    for chunk in plan.chunks:
        try:
            review = provider.complete_json(system, build_user(chunk), Review)
        except LLMError as exc:
            log.error("review failed for %s: %s", chunk.path, exc)
            if chunk.path not in result.failed:
                result.failed.append(chunk.path)
            continue
        raw.extend(review.findings)
        result.summaries.append(review.summary)

    post = postprocess(raw, kept, min_confidence)
    result.inline, result.low_confidence, result.dropped = (
        post.inline,
        post.low_confidence,
        post.dropped,
    )
    result.usage = provider.usage
    return result
