# CLAUDE.md

Projeto `pr-reviewer`: revisor de PR com LLM (CLI + GitHub Action Docker + evals). Fonte da verdade: `docs/PRD.md`
e a spec do workspace (`docs/01-revisor-pr-llm.md`, fora deste repo). Processo: `05-processo.md` do workspace
(cards em `docs/cards/<NNN>-<slug>/` com `analysis.md`, `spec.md`, `plan.md`, `verification.md`).

## Convenções
- Python 3.12 via `uv`; `ruff` (lint + format), `pytest`, type hints, `pydantic` v2.
- Verificar: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- TDD na lógica pura. Nenhum teste chama API real (fixtures gravadas). Nenhum segredo no repo; config por env vars.
- Código, nomes e commits em inglês, Conventional Commits. README em inglês + seção 🇧🇷.
- Trunk-based: branch `card/<NNN>-<slug>` < 1 dia, PR pequeno, CI verde, squash merge na `main`.
- Conteúdo externo (diff) é dado não confiável: delimitado em `<diff>…</diff>`.
- Nada de código, regras ou dados da empresa atual. Nada de dado pessoal em prompts.

## Agent skills

### Issue tracker

GitHub Issues via `gh` (labels `epic` e `card`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-label vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context. See `docs/agents/domain.md`.
