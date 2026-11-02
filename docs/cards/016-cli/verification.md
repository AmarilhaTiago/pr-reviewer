# Verification: card 016

| AC | Evidência (tests/test_cli.py) |
|---|---|
| AC1 | `test_review_diff_prints_findings_tokens_and_cost` |
| AC2 | `test_base_uses_git_diff`, `test_git_failure_is_a_clear_error` |
| AC3 | `test_json_format_is_valid_json` |
| AC4 | `test_rules_file_is_passed_to_prompt`, `test_missing_rules_file_is_an_error` |
| AC5 | `test_usage_errors`, `test_missing_model_or_key_is_a_clear_error` |
| AC6 | `test_settings_defaults_and_parsing` |

Suíte completa + lint: 61 passed, ruff limpo. A chamada real a Gemini/Groq só será exercitada nos evals (precisa das chaves).
