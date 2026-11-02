# Verification: card 015

| AC | Evidência |
|---|---|
| AC1 | `tests/test_prompt.py::test_system_prompt_sets_role_and_injection_guard`, `::test_system_prompt_includes_team_rules` |
| AC2 | `tests/test_prompt.py::test_user_prompt_wraps_chunk_in_diff_tags`, `::test_closing_tag_inside_diff_is_neutralized` |
| AC3 | `tests/test_pipeline.py::test_pipeline_end_to_end_with_fake_llm`, `::test_budget_skips_are_reported` |
| AC4 | `tests/test_pipeline.py::test_llm_error_in_one_chunk_does_not_stop_others` |
| AC5 | `tests/test_pipeline.py::test_empty_or_fully_ignored_diff_makes_no_calls` |

Suíte completa + lint: 52 passed, ruff limpo.
