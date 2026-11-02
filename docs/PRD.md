# PRD: pr-reviewer

> Fonte: `docs/01-revisor-pr-llm.md` do workspace (spec) + descoberta de 02/11/2026. Em caso de conflito, este PRD vence.

## Problema
Times pequenos gastam tempo de revisão humana com o óbvio (bugs simples, segurança, convenções). Falta uma primeira revisão automática que seja confiável, barata e mensurável.

## Usuário
Time pequeno que quer uma primeira revisão automática no PR antes da revisão humana. O revisor **não substitui** a pessoa revisora.

## Objetivos
1. CLI local (`reviewer review`, `reviewer evals`) que revisa um diff e imprime achados por severidade + tokens e custo.
2. GitHub Action (Docker) que publica review inline e resumo idempotente (`<!-- pr-reviewer -->`) a cada push.
3. Saída de LLM validada por schema (Pydantic), com 1 retry e registro de falha.
4. Evals com ~16 casos (PHP e Python, 3 a 4 limpos) e métricas: precisão, recall, falso positivo, custo e latência médios; Gemini vs Groq.
5. README no template de 9 itens, com GIF e tabela de evals (só números medidos).

## Não-objetivos
Corrigir automaticamente ou abrir commits; interface web; GitLab/Bitbucket; arquivos binários; publicar no PyPI.

## Requisitos funcionais
- RF1 Parse de diff unificado (arquivos, hunks, linhas adicionadas com número no arquivo novo).
- RF2 Filtro de arquivos ignorados por glob configurável.
- RF3 Chunking por arquivo e por hunk (`MAX_TOKENS_PER_CHUNK`); orçamento por PR (`MAX_TOKENS_PER_PR`) com aviso dos arquivos omitidos.
- RF4 Prompt com `rules.md` do time e diff delimitado em `<diff>…</diff>` como dado não confiável.
- RF5 Pós-processamento: descarta linhas fora do diff; `confidence < MIN_CONFIDENCE` (0,5) vai só ao resumo; dedupe (arquivo, linha ±2, categoria).
- RF6 Provedores: `OpenAICompatibleProvider` (Gemini padrão, Groq) e Anthropic opcional; `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`.
- RF7 Action: review inline (`path`, `line`, `side: RIGHT`), resumo com tabela por severidade, veredito, ignorados, tokens e custo; permissões `pull-requests: write`, `contents: read`.
- RF8 Workflow `self-review.yml` (dogfooding) e `ci.yml` (ruff + pytest).

## Requisitos não funcionais
- Custo zero: free tier; nenhum teste chama API real (fixtures gravadas).
- Sem segredo no repo ou no histórico; nenhum dado pessoal no prompt.
- Erro 429: 1 retry com espera, depois registra e segue sem quebrar.
- Python 3.12, `uv`, `ruff`, `pytest`, type hints, `pydantic` v2.

## Métricas de sucesso
Critérios de aceite da spec §8 atendidos; frase do formulário preenchida com números medidos.

## Decisões (com o porquê)
| # | Decisão | Por quê |
|---|---|---|
| P1 | `action.yml` **Docker** (`Dockerfile` instala o pacote com `uv`) | Escolha do Tiago: ambiente isolado e reproduzível; custo é uma primeira execução mais lenta. |
| P2 | Módulo `llm/` **copiado** entre repos | Repos separados e prazo curto; evita publicar e versionar um pacote. |
| P3 | Pacote `reviewer` com `typer`, sem PyPI | Menos peças; a Action instala do próprio repo. |
| P4 | Orçamento conservador: `MAX_TOKENS_PER_CHUNK=6000`, `CALL_INTERVAL_SECONDS=2`; ajustar quando os limites reais chegarem | Limites do free tier não são publicados com números. |
| P5 | Tokens estimados por `len(texto)/4` só para dividir blocos; custo e tokens reportados vêm do `usage` da API | Sem tokenizer por provedor; o dado reportado é o real. |
| P6 | Casos de eval escritos por Claude, `expected.json` revisados em lote pelo Tiago antes de rodar | Velocidade; nada de código da empresa. |
| P7 | Licença MIT | Padrão de portfólio. |

## Riscos
- Limites do free tier podem estourar nos evals → intervalo entre chamadas, blocos menores, registrar e seguir.
- Endpoint compatível com OpenAI e JSON estruturado de Gemini/Groq **não confirmados** → verificar na doc oficial no card do provedor.
- PRs de forks não têm acesso aos secrets → documentar.
- Primeira execução Docker mais lenta → aceitável.
