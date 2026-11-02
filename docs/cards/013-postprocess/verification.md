# Verification: card 013

| AC | Evidência (tests/test_postprocess.py) |
|---|---|
| AC1 | `test_findings_outside_diff_are_dropped`, `test_context_lines_are_valid` |
| AC2 | `test_low_confidence_goes_to_summary_only` |
| AC3 | `test_duplicates_keep_highest_severity_then_confidence`, `test_different_category_or_distance_not_duplicate` |
| AC4 | `test_sorted_by_severity_file_line` |

Suíte completa + lint: verde.
