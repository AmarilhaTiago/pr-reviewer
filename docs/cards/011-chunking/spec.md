# Card 011: Chunking e orçamento por PR (spec + plan)

Contrato (`reviewer/chunking.py`):
- `estimate_tokens(text) -> int` = `ceil(len/4)` (só para dividir; custo real vem do `usage`).
- `Chunk(path, text, added_lines, tokens)`; `text` = `"File: <path>\n"` + hunks (`Hunk.raw`) separados por linha em branco.
- `ChunkPlan(chunks, skipped)`; `build_chunks(files, max_tokens_per_chunk, max_tokens_per_pr) -> ChunkPlan`.

Regras:
- AC1: arquivo que cabe em `max_tokens_per_chunk` -> 1 chunk.
- AC2: arquivo acima do limite -> agrupa hunks em ordem, sem estourar o limite; um hunk sozinho maior que o limite vira chunk próprio (não se divide mais).
- AC3: orçamento: arquivos considerados em ordem decrescente de linhas alteradas (`+`/`-`); um arquivo entra inteiro se couber no restante de `max_tokens_per_pr`, senão vai para `skipped` (continua tentando os menores). `skipped` lista os caminhos omitidos.
- AC4: arquivos sem hunks (rename puro, binário) não geram chunk. `added_lines` do chunk cobre só as linhas dos seus hunks.

Plan (TDD): `tests/test_chunking.py` -> implementar.
