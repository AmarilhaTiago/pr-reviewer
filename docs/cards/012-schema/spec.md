# Card 012: Schema Finding/Review (spec + plan)

Contrato (`reviewer/schema.py`), conforme spec 3.3: `Finding(file, line, severity, category, title<=80, explanation, suggestion|None, confidence 0..1)`, `Review(findings, summary)`.
- AC1: JSON válido valida (`Review.model_validate_json`); `suggestion` opcional.
- AC2: `severity`/`category` fora dos literais, `title` > 80, `confidence` fora de 0..1 ou `line` < 1 -> `ValidationError`.
- AC3: `Review.findings` default vazio não existe: campos obrigatórios ausentes falham (summary é obrigatório).

Plan: `tests/test_schema.py` -> implementar.
