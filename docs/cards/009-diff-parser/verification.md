# Verification: card 009

| AC | Evidência (tests/test_diff.py) |
|---|---|
| AC1 | `test_two_files_with_hunks` |
| AC2 | `test_added_line_numbers_in_new_file`, `test_removed_lines_have_no_number` |
| AC3 | `test_new_file`, `test_deleted_file`, `test_pure_rename_without_hunks`, `test_binary_file` |
| AC4 | `test_no_newline_marker_ignored_and_empty_input` |

Suíte completa + lint: `ruff check`, `ruff format --check`, `pytest` -> 9 passed.
