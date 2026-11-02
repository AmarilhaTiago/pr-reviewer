# Card 044: Numerar as linhas do diff no prompt (spec + plan)

Hipótese (a testar, não assumida): parte dos erros de linha do modelo vem de ele ter que contar a partir do cabeçalho do hunk. Se numerar as linhas ajudar, recall e precisão sobem; se não, o resultado é publicado do mesmo jeito.

Contrato:
- `Hunk.numbered` (em `reviewer/diff.py`): cabeçalho do hunk + cada linha como `"{n:>5} {kind}{texto}"` para `+` e ` ` (n = linha no arquivo novo) e `"      -{texto}"` para `-` (sem número).
- `build_chunks` usa `Hunk.numbered` no texto do chunk (o texto do arquivo continua começando por `File: <path>`).
- `SYSTEM` (em `reviewer/prompt.py`) explica o prefixo e manda citar esses números.

ACs:
- AC1: linhas `+` e de contexto saem com o número do arquivo novo; linhas `-` saem sem número (verificado com um hunk que começa em linha > 1 e mistura `-`, `+` e contexto).
- AC2: o texto do chunk contém as linhas numeradas, e `added_lines` do chunk não muda.
- AC3: o system prompt menciona o prefixo de numeração.
- AC4: antes/depois medidos (Gemini e Groq, 16 casos) e publicados no README; os JSON "antes" ficam em `evals/results/before-line-numbers/`.

Plan (TDD): testes em `tests/test_diff.py`, `tests/test_chunking.py`, `tests/test_prompt.py` -> `Hunk.numbered` -> `chunking._make_chunk` -> `SYSTEM` -> rodar evals -> README.
