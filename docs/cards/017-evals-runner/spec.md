# Card 017: Evals, métricas e runner (spec + plan)

Formato de caso: `evals/cases/<nome>/{diff.patch, expected.json, README.md}`; `expected.json` = `{"expected": [{"file", "line", "category"}]}`. Caso limpo = lista vazia.

Contrato (`reviewer/evals/`):
- `metrics.py`: `is_match(finding, expected, tolerance=3)` (mesmo arquivo, |linha| <= 3, mesma categoria); `score_case(findings, expected) -> CaseScore(tp, fp, fn)` com casamento um-para-um; `aggregate(scores) -> Metrics(precision, recall, false_positive_rate, ...)`.
- `runner.py`: `load_cases(dir)`, `run_evals(cases, provider, model, *, rules, settings, clock) -> EvalReport` com resultado por caso (achados, latência, tokens, custo).
- `report.py`: `write_results(report, out_dir, date) -> Path` (`<data>-<modelo>.json`) e `render_table(report) -> str` (Markdown).
- CLI: `reviewer evals [--model X] [--cases DIR] [--out DIR] [--rules PATH]`.

ACs:
- AC1: `is_match` exige arquivo, categoria e linha dentro de ±3; `score_case` casa um-para-um (um achado não cobre dois esperados; sobra vira FP).
- AC2: precisão = TP/(TP+FP), recall = TP/(TP+FN) (None se denominador 0); taxa de falso positivo = casos limpos com >=1 achado / casos limpos (None sem casos limpos).
- AC3: `load_cases` lê os casos em ordem alfabética; erro claro se `expected.json` ou `diff.patch` faltar.
- AC4: o runner executa o pipeline por caso, mede latência (relógio injetável), tokens e custo por caso (diferença do `usage` do provedor); LLMError no caso vira caso com `error` e conta como sem achados.
- AC5: `write_results` grava JSON com métricas e casos; `render_table` gera tabela Markdown com precisão, recall, FP, custo médio e latência média (`n/a` quando indefinido).
- AC6: `reviewer evals` roda os casos com o provedor das env vars, `--model` sobrescreve `LLM_MODEL`, grava o resultado e imprime a tabela.

Plan (TDD): `tests/test_evals.py` (provedor falso, casos em tmp_path) -> implementar.
