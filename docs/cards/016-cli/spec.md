# Card 016: CLI `reviewer review` (spec + plan)

Contrato:
- `reviewer/config.py`: `Settings.from_env(env)` lê `LLM_PROVIDER` (padrão `gemini`), `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL`, `MAX_TOKENS_PER_CHUNK` (6000), `MAX_TOKENS_PER_PR` (60000), `MIN_CONFIDENCE` (0.5), `CALL_INTERVAL_SECONDS` (2), `IGNORE_GLOBS` (CSV; vazio = padrões).
- `reviewer/render.py`: `render_markdown(result, model, cost)`, `render_json(result, model, cost)`.
- `reviewer/cli.py` (`typer`): `reviewer review (--diff PATH | --base REF) [--rules PATH] [--format md|json]`. `--base` roda `git diff REF...HEAD`. Faz `load_dotenv` simples de `.env` se existir (sem sobrescrever o ambiente).
- Exemplo de regras versionado em `.reviewer/rules.md` (PHP/Laravel e Python, escrito do zero).

ACs:
- AC1: `review --diff x.diff` imprime achados agrupados por severidade (blocker, major, minor), seguidos de baixa confiança, arquivos ignorados/omitidos/falhos, tokens e custo (`n/a` sem preço).
- AC2: `--base REF` obtém o diff via `git diff REF...HEAD`; erro do git -> mensagem clara e saída 2.
- AC3: `--format json` emite JSON válido com `findings`, `low_confidence`, `ignored`, `skipped`, `failed`, `usage` e `cost_usd`.
- AC4: `--rules` lido e passado ao pipeline; arquivo ausente -> erro claro (saída 2).
- AC5: sem `--diff`/`--base` ou com ambos -> erro de uso (saída 2); sem `LLM_API_KEY`/modelo -> mensagem clara (saída 2), sem traceback.
- AC6: config: padrões, parsing de números e `IGNORE_GLOBS`.

Plan (TDD): `tests/test_config.py`, `tests/test_render.py`, `tests/test_cli.py` (typer `CliRunner`, provedor injetado via `make_provider` monkeypatch) -> implementar.
