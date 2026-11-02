# Card 013: Pós-processamento (spec + plan)

Contrato (`reviewer/postprocess.py`): `postprocess(findings, files, min_confidence=0.5) -> PostResult(inline, low_confidence, dropped)`.
- Linha válida = número de linha do arquivo novo presente em algum hunk (linha `+` ou de contexto) do arquivo do achado.
- AC1: achado em arquivo/linha que não está no diff é descartado e contado em `dropped`.
- AC2: `confidence < min_confidence` vai para `low_confidence` (só resumo), os demais para `inline`.
- AC3: duplicata = mesmo arquivo, |linha| <= 2 e mesma categoria; fica a de maior severidade (blocker > major > minor), depois maior confiança. Dedupe vale dentro de cada grupo.
- AC4: saída ordenada por severidade, depois arquivo e linha.

Plan: `tests/test_postprocess.py` -> implementar.
