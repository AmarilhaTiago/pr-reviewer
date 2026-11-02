# Verification: card 044

| AC | Evidência |
|---|---|
| AC1 | `tests/test_diff.py::test_numbered_hunk_prefixes_new_file_line_numbers` |
| AC2 | `tests/test_chunking.py::test_chunk_text_has_numbered_lines_and_added_lines_unchanged` |
| AC3 | `tests/test_prompt.py::test_system_prompt_explains_line_number_prefix` |
| AC4 | `evals/results/before-line-numbers/` e `evals/results/after-line-numbers/` (2 rodadas por modelo); tabela e leitura no README |

Resultado (medido, não assumido): Groq melhorou nas duas rodadas (recall 85% para 100%/92%, precisão 79% para 87%/86%); Gemini inconclusivo (recall 100% e 77% contra 92% duas vezes antes).
Suíte completa + lint: 102 passed, ruff limpo.
