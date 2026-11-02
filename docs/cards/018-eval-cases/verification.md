# Verification: card 018

| AC | Evidência |
|---|---|
| AC1 | `tests/test_eval_cases.py::test_case_mix`, `::test_categories_cover_the_planned_kinds`, `::test_every_case_has_a_readme` (16 casos: 13 com bug, 3 limpos; 7 PHP, 9 Python) |
| AC2 | `tests/test_eval_cases.py::test_expected_lines_point_at_added_lines_of_the_right_file` |
| AC3 | **Pendente:** revisão dos `expected.json` pelo Tiago |

Suíte completa + lint: 73 passed, ruff limpo.
