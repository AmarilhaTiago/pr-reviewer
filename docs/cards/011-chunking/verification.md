# Verification: card 011

| AC | Evidência (tests/test_chunking.py) |
|---|---|
| AC1 | `test_small_file_is_one_chunk` |
| AC2 | `test_large_file_splits_by_hunks`, `test_oversized_single_hunk_gets_own_chunk` |
| AC3 | `test_budget_skips_files_that_do_not_fit_largest_change_first` |
| AC4 | `test_files_without_hunks_make_no_chunk_and_skip_not_reported` |

Suíte completa + lint: 18 passed, ruff limpo.
