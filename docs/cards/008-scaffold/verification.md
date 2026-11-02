# Verification: card 008

| AC | Evidência |
|---|---|
| AC1 | `uv run ruff check . && uv run ruff format --check . && uv run pytest` -> All checks passed, 1 passed |
| AC2 | `.github/workflows/ci.yml`; run do CI verde no PR |
| AC3 | `.env.example` versionado; `.gitignore` ignora `.env` e `.env.*` |
