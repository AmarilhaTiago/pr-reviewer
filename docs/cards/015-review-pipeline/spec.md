# Card 015: Prompt e pipeline de revisão (spec + plan)

Contrato:
- `reviewer/prompt.py`: `build_system(rules: str = "") -> str`, `build_user(chunk: Chunk) -> str`.
- `reviewer/pipeline.py`: `review_diff(diff_text, provider, *, rules="", ignore_patterns=DEFAULT_IGNORE, max_tokens_per_chunk=6000, max_tokens_per_pr=60000, min_confidence=0.5) -> ReviewResult`.
- `ReviewResult(inline, low_confidence, dropped, ignored, skipped, failed, summaries, usage)`; `ignored`/`skipped`/`failed` são listas de caminhos.

ACs:
- AC1: o system prompt define o papel de revisor sênior (bugs, segurança, performance, convenções; sem comentário cosmético sem regra), manda tratar o conteúdo de `<diff>` como dado e ignorar instruções dentro dele, e inclui o `rules.md` quando fornecido.
- AC2: o user prompt traz o chunk entre `<diff>` e `</diff>`; ocorrências de `</diff>` dentro do conteúdo são neutralizadas (não encerram o bloco).
- AC3: pipeline: parse -> filtro -> chunks -> LLM por chunk -> pós-processamento; devolve achados filtrados, `ignored`, `skipped` e `usage` do provedor.
- AC4: `LLMError` em um chunk entra em `failed` (caminho) e os demais chunks seguem.
- AC5: diff vazio ou só com arquivos ignorados -> resultado vazio sem chamar o LLM.

Plan (TDD): `tests/test_prompt.py`, `tests/test_pipeline.py` (provedor falso) -> `prompt.py` -> `pipeline.py`.
