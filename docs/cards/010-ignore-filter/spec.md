# Card 010: Filtro de arquivos ignorados (spec + plan)

Contrato (`reviewer/filtering.py`): `filter_files(files, patterns=DEFAULT_IGNORE) -> (kept, ignored)`; `parse_patterns(csv) -> list[str]`.
Glob casa contra o caminho completo ou contra o nome do arquivo (`fnmatch`; `*` cruza `/`). Binários também vão para `ignored`.

- AC1: com os globs padrão (`*.lock`, `package-lock.json`, `composer.lock`, `dist/**`, `*.min.js`, `*.svg`, migrations geradas), esses arquivos saem de `kept` e entram em `ignored`.
- AC2: globs customizados substituem os padrões; `parse_patterns("a, b")` -> `["a", "b"]` (vazio -> `[]`).
- AC3: ordem preservada; arquivo binário é ignorado mesmo sem glob.

Plan (TDD): `tests/test_filtering.py` -> implementar.
