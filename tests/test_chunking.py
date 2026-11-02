from reviewer.chunking import build_chunks, estimate_tokens
from reviewer.diff import DiffLine, FileDiff, Hunk


def hunk(start: int, n: int, width: int = 40) -> Hunk:
    lines = [DiffLine("+", "x" * width, start + i) for i in range(n)]
    return Hunk(header=f"@@ -0,0 +{start},{n} @@", new_start=start, lines=lines)


def file(path: str, *hunks: Hunk) -> FileDiff:
    return FileDiff(path=path, hunks=list(hunks))


def test_estimate_tokens_is_ceil_len_over_4():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2


def test_small_file_is_one_chunk():  # AC1
    plan = build_chunks([file("a.py", hunk(1, 2))], 1000, 10_000)
    assert len(plan.chunks) == 1
    c = plan.chunks[0]
    assert c.path == "a.py" and c.text.startswith("File: a.py\n")
    assert c.added_lines.keys() == {1, 2} and plan.skipped == []


def test_large_file_splits_by_hunks():  # AC2
    f = file("big.py", hunk(1, 3), hunk(100, 3), hunk(200, 3))
    one = estimate_tokens(hunk(1, 3).numbered)
    plan = build_chunks([f], max_tokens_per_chunk=one * 2 + 5, max_tokens_per_pr=10_000)
    assert [sorted(c.added_lines) for c in plan.chunks] == [
        [1, 2, 3, 100, 101, 102],
        [200, 201, 202],
    ]


def test_oversized_single_hunk_gets_own_chunk():  # AC2
    plan = build_chunks([file("a.py", hunk(1, 50), hunk(100, 1))], 10, 10_000)
    assert [len(c.added_lines) for c in plan.chunks] == [50, 1]


def test_budget_skips_files_that_do_not_fit_largest_change_first():  # AC3
    big, mid, small = file("big", hunk(1, 20)), file("mid", hunk(1, 10)), file("small", hunk(1, 1))
    budget = estimate_tokens(big.hunks[0].raw) + 60  # big + small fit, mid does not
    plan = build_chunks([small, mid, big], 10_000, budget)
    assert [c.path for c in plan.chunks] == ["big", "small"]
    assert plan.skipped == ["mid"]


def test_files_without_hunks_make_no_chunk_and_skip_not_reported():  # AC4
    plan = build_chunks([file("renamed.py"), file("a.py", hunk(1, 1))], 1000, 10_000)
    assert [c.path for c in plan.chunks] == ["a.py"] and plan.skipped == []


def test_chunk_text_has_numbered_lines_and_added_lines_unchanged():  # AC2
    plan = build_chunks([file("a.py", hunk(7, 2))], 1000, 10_000)
    (chunk,) = plan.chunks
    assert f"    7 +{'x' * 40}" in chunk.text and f"    8 +{'x' * 40}" in chunk.text
    assert sorted(chunk.added_lines) == [7, 8]
