# Verification: card 021

| AC | Evidência |
|---|---|
| AC1 | `tests/test_action.py::test_action_inputs_match_the_spec`, `::test_action_is_docker_and_args_follow_entrypoint_order` |
| AC2 | Job `docker` do CI: `docker build` + `reviewer --help` na imagem (Docker local indisponível) |
| AC3 | `tests/test_action.py::test_self_review_workflow_permissions_and_dogfooding`; execução real depende do secret `GEMINI_API_KEY` e da variável `LLM_MODEL` |
| AC4 | `tests/test_action.py::test_entrypoint_skips_without_api_key` + CI: `docker run` sem chave imprime "skipped" |
| AC5 | Pendente no card 022 (README) |

Suíte completa + lint: 88 passed, ruff limpo.
