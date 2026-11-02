# Verification: card 017

| AC | Evidência (tests/test_evals.py) |
|---|---|
| AC1 | `test_is_match_requires_file_category_and_line_within_3`, `test_score_case_matches_one_to_one` |
| AC2 | `test_aggregate_metrics`, `test_aggregate_undefined_values_are_none` |
| AC3 | `test_load_cases_sorted_and_validated` |
| AC4 | `test_runner_measures_latency_tokens_cost_and_errors` |
| AC5 | `test_results_file_and_table` |
| AC6 | `test_cli_evals_command` |

Suíte completa + lint: 69 passed, ruff limpo. Os casos reais ficam no card 018; a execução com LLM real, no 019.
