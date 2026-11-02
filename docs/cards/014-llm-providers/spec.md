# Card 014: Provedores LLM (spec + plan)

Verificado em 02/11/2026 nas docs oficiais: Groq `https://api.groq.com/openai/v1` + `response_format: json_schema` (modelos gpt-oss);
Gemini `https://generativelanguage.googleapis.com/v1beta/openai/` aceita saída estruturada (há relatos de instabilidade em fóruns, então validamos sempre com Pydantic).

Contrato (`reviewer/llm/`):
- `LLMProvider.complete_json(system, user, schema) -> BaseModel`; `provider.usage` acumula `Usage(prompt_tokens, completion_tokens, calls)`; falha final -> `LLMError`.
- `OpenAICompatibleProvider(base_url, api_key, model, client=None, min_interval=0, sleep, clock)` -> `POST {base_url}/chat/completions`, Bearer.
- `make_provider(provider, model, api_key, base_url=None, **kw)`: presets `gemini`, `groq`; `openai-compatible` exige `base_url`. `anthropic` fica fora deste card (opcional pago; cortado por escopo).
- `cost.estimate_cost(model, usage, prices) -> float | None` (US$; `None` se o modelo não está na tabela `reviewer/prices.json`; preços só entram quando verificados na doc oficial).

ACs:
- AC1: resposta válida -> instância do schema; o request leva modelo, Bearer, `response_format` json_schema e o schema no system prompt.
- AC2: JSON inválido/fora do schema -> 1 retry com o erro de validação na conversa; segundo erro -> `LLMError` (o chamador registra e segue). JSON dentro de cerca ``` é aceito.
- AC3: HTTP 429 -> espera `Retry-After` (teto 60 s, padrão 5 s) e 1 retry; novo 429 -> `LLMError`. Outros HTTP >= 400 e erros de rede -> `LLMError`.
- AC4: HTTP 400 com `json_schema` -> fallback único (sticky) para `json_object`.
- AC5: tokens do `usage` da API somados por chamada (inclui retries); `min_interval` espaça chamadas consecutivas.
- AC6: `make_provider` com presets, erro claro para provedor desconhecido ou chave vazia.
- AC7: `estimate_cost` devolve US$ com tabela por 1M tokens; `None` sem preço.

Plan (TDD): `tests/test_llm.py` com `httpx.MockTransport` e fixture de resposta no formato documentado da API (sintética, pois ainda não há chaves; gravações reais entram nos evals) -> `base.py`, `openai_compatible.py`, `factory.py`, `cost.py`.
