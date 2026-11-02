# Verification: card 014

| AC | Evidência (tests/test_llm.py) |
|---|---|
| AC1 | `test_valid_response_returns_schema_instance` |
| AC2 | `test_invalid_json_retries_once_with_error_then_succeeds`, `test_second_invalid_response_raises_llm_error`, `test_fenced_json_is_accepted` |
| AC3 | `test_429_waits_retry_after_and_retries_once`, `test_429_twice_raises_and_wait_is_capped`, `test_other_http_errors_and_network_errors_raise` |
| AC4 | `test_400_falls_back_to_json_object_and_sticks` |
| AC5 | `test_usage_is_summed_across_calls_and_retries`, `test_min_interval_spaces_consecutive_calls` |
| AC6 | `test_factory_presets_and_errors` |
| AC7 | `test_estimate_cost` |

Suíte completa + lint: 44 passed, ruff limpo. Fixture de resposta é sintética (formato documentado da API); gravações reais ficam para os evals.
Fora do escopo (decidido): provedor Anthropic (opcional pago) e preços reais em `prices.json` (só com valor verificado na doc oficial).
