# Card 009: Parser de diff unificado (spec + plan)

Contrato (`reviewer/diff.py`): `parse_diff(text: str) -> list[FileDiff]`.
- `FileDiff(path, old_path, status, is_binary, hunks)`; `status` in `added|modified|deleted|renamed`; `path` = caminho novo (ou antigo se deletado).
- `Hunk(header, new_start, lines)`; `DiffLine(kind, text, new_number)`; `kind` in `+|-| `; `new_number` = linha no arquivo novo (None para `-`).
- `FileDiff.added_lines` -> `{numero: texto}` das linhas adicionadas; `Hunk.raw` -> texto do hunk (header + linhas).

ACs:
- AC1: diff com N arquivos e hunks -> N FileDiff com hunks corretos.
- AC2: cada linha `+` tem número correto no arquivo novo (contexto e `+` avançam; `-` não).
- AC3: renomeação (`rename from/to`), arquivo novo/removido e binário (`Binary files ... differ`) não quebram; binário -> `is_binary=True`, sem hunks.
- AC4: `\ No newline at end of file` é ignorado; entrada vazia -> `[]`.

Plan (TDD): um teste por AC em `tests/test_diff.py` -> implementar parser linha a linha -> refatorar.
