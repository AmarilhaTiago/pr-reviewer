# Card 008: Scaffold (spec + plan)

ACs (issue #8):
- AC1: `uv run ruff check . && uv run ruff format --check . && uv run pytest` passa no repo limpo.
- AC2: CI (push/PR) roda ruff e pytest.
- AC3: `.env.example` versionado, `.env` ignorado.

Plan: pyproject (hatchling, python 3.12, typer/pydantic/httpx; dev ruff/pytest) -> `reviewer/__init__.py` com `__version__` ->
teste de importação (AC1) -> `.github/workflows/ci.yml` (AC2) -> `.env.example`, `.gitignore` (AC3).
