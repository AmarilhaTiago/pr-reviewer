# Card 020: Publicação no GitHub (spec + plan)

Contrato:
- `reviewer/summary.py`: `MARKER = "<!-- pr-reviewer -->"`, `verdict(findings)`, `render_summary(result, model, cost, *, hidden=0, unplaced=())`, `inline_body(finding)`, `fingerprint(finding)`.
- `reviewer/github.py`: `GitHubClient(token, repo, client=None, api_url)` com `get_diff(pr)`, `existing_fingerprints(pr)`, `post_review(pr, comments) -> bool`, `upsert_summary(pr, body)`; `publish(gh, pr, result, model, cost, min_severity)`.
- CLI `reviewer pr --number N [--repo owner/name] [--rules PATH] [--min-severity minor|major|blocker] [--dry-run]`: `GITHUB_TOKEN`, `GITHUB_REPOSITORY` e (sem `--number`) o PR do `GITHUB_EVENT_PATH`; busca o diff pela API (`Accept: application/vnd.github.diff`).

ACs:
- AC1: a review é um `POST /repos/{repo}/pulls/{n}/reviews` com `event: COMMENT` e comentários inline `{path, line, side: "RIGHT", body}`, um por achado (apenas severidade >= `min_severity`).
- AC2: o resumo traz o marcador, veredito (⛔ se há blocker, ⚠️ se há major/minor, ✅ se nada), tabela por severidade, achados de baixa confiança, arquivos ignorados/omitidos/falhos, tokens e custo (`n/a` sem preço).
- AC3: idempotência do resumo: se já existe comentário com o marcador no PR, é atualizado (`PATCH /issues/comments/{id}`); senão é criado (`POST /issues/{n}/comments`). Nunca dois.
- AC4: achados cujo fingerprint (`<!-- pr-reviewer:<hash> -->` no corpo) já existe em comentários da review não são repostados em novo push.
- AC5: se a API rejeitar a review (422), nada inline é postado e os achados vão para o resumo como "não posicionados"; o fluxo não quebra.
- AC6: `get_diff` usa o media type de diff; erros HTTP (>= 400) viram `GitHubError` com status e corpo curto; paginação (`per_page=100`) até esgotar.
- AC7: `reviewer pr --dry-run` imprime o resumo e não chama a API de escrita; sem token/repo -> erro claro (saída 2).

Plan (TDD): `tests/test_summary.py`, `tests/test_github.py` (`httpx.MockTransport`; respostas no formato documentado da API REST do GitHub), `tests/test_cli_pr.py` -> implementar.
