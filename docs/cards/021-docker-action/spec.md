# Card 021: Dockerfile, action.yml e self-review (spec + plan)

ACs:
- AC1: `action.yml` (Docker) com inputs `provider` (padrão `gemini`), `model`, `api-key`, `rules-path`, `min-severity`, `max-tokens-per-pr` (+ `github-token`), repassados ao `entrypoint.sh` por argumentos posicionais.
- AC2: a imagem constrói e expõe o CLI `reviewer` (verificado no CI: `docker build` + `reviewer --help`).
- AC3: `self-review.yml` roda a action (`uses: ./`) nos PRs do próprio repo com `contents: read` e `pull-requests: write`. Parâmetros: secret `GEMINI_API_KEY` e variável `LLM_MODEL` (o Tiago cadastra).
- AC4: sem API key (PR de fork, sem secrets) o entrypoint avisa e sai com 0, sem falhar o check.
- AC5: limitação de forks documentada (README, card 022).

Plan: testes estruturais do `action.yml`/workflow/entrypoint -> Dockerfile, entrypoint, action.yml, workflow -> job `docker` no CI. O build local não foi possível (Docker Desktop desligado); a evidência do AC2 é o CI.
