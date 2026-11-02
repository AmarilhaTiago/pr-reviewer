# Card 018: Casos de eval (spec + plan)

ACs:
- AC1: 16 casos em `evals/cases/<nome>/` (`diff.patch`, `expected.json`, `README.md`): 13 com bug plantado (segurança, bug, performance, convenção) e 3 limpos; 7 PHP/Laravel e 9 Python. Escritos do zero, sem nada da empresa.
- AC2: o `expected.json` de cada caso aponta uma linha adicionada do arquivo certo (verificado por teste), com a categoria do bug plantado.
- AC3: os `expected.json` são revisados pelo Tiago em lote antes da rodada real (card 019).

Plan: gerador com `difflib` (diff e número de linha exatos; script fora do repo) -> `tests/test_eval_cases.py` valida a estrutura -> commit.
