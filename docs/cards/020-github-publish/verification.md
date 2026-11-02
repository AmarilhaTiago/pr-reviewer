# Verification: card 020

| AC | Evidência |
|---|---|
| AC1 | `tests/test_github.py::test_review_has_inline_comments_with_right_side`, `::test_min_severity_filters_inline_comments` |
| AC2 | `tests/test_github.py::test_summary_content` |
| AC3 | `tests/test_github.py::test_summary_is_created_then_updated_never_duplicated` |
| AC4 | `tests/test_github.py::test_already_posted_findings_are_not_reposted` |
| AC5 | `tests/test_github.py::test_rejected_review_moves_findings_to_summary` |
| AC6 | `tests/test_github.py::test_get_diff_uses_diff_media_type_and_errors_are_clear`, `::test_pagination_collects_all_pages` |
| AC7 | `tests/test_cli_pr.py` (3 testes) |

Suíte completa + lint: 84 passed, ruff limpo. A API real do GitHub só é exercitada no self-review do card 021 (as respostas dos testes seguem o formato documentado da REST API).
