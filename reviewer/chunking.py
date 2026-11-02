"""Split a parsed diff into LLM-sized chunks under a per-PR token budget."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from reviewer.diff import FileDiff, Hunk


def estimate_tokens(text: str) -> int:
    """Rough estimate (chars / 4); only used to size chunks, billing uses API usage."""
    return -(-len(text) // 4)


@dataclass
class Chunk:
    path: str
    text: str
    added_lines: dict[int, str]
    tokens: int


@dataclass
class ChunkPlan:
    chunks: list[Chunk] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _change_size(f: FileDiff) -> int:
    return sum(1 for h in f.hunks for line in h.lines if line.kind != " ")


def _make_chunk(path: str, hunks: list[Hunk]) -> Chunk:
    text = f"File: {path}\n" + "\n\n".join(h.numbered for h in hunks)
    added = {
        line.new_number: line.text
        for h in hunks
        for line in h.lines
        if line.kind == "+" and line.new_number is not None
    }
    return Chunk(path=path, text=text, added_lines=added, tokens=estimate_tokens(text))


def _split_file(f: FileDiff, max_tokens: int) -> list[Chunk]:
    whole = _make_chunk(f.path, f.hunks)
    if whole.tokens <= max_tokens:
        return [whole]
    chunks: list[Chunk] = []
    group: list[Hunk] = []
    for h in f.hunks:
        candidate = _make_chunk(f.path, [*group, h])
        if group and candidate.tokens > max_tokens:
            chunks.append(_make_chunk(f.path, group))
            group = [h]
        else:
            group.append(h)
    if group:
        chunks.append(_make_chunk(f.path, group))
    return chunks


def build_chunks(
    files: Iterable[FileDiff], max_tokens_per_chunk: int, max_tokens_per_pr: int
) -> ChunkPlan:
    plan = ChunkPlan()
    remaining = max_tokens_per_pr
    candidates = [f for f in files if f.hunks]
    for f in sorted(candidates, key=_change_size, reverse=True):
        chunks = _split_file(f, max_tokens_per_chunk)
        cost = sum(c.tokens for c in chunks)
        if cost <= remaining:
            plan.chunks.extend(chunks)
            remaining -= cost
        else:
            plan.skipped.append(f.path)
    return plan
