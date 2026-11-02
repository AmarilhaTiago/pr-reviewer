# Example team rules

Example conventions for a small PHP/Laravel + Python team. Replace with your own.

## PHP / Laravel
- Compare with `===` / `!==`; flag loose `==` comparisons on user input or IDs.
- Never build SQL by concatenating variables; use bindings or the query builder.
- Do not run queries inside loops; eager load relations with `with()` to avoid N+1.
- Escape output in Blade with `{{ }}`; flag `{!! !!}` on user-controlled data.
- Validate request input with Form Requests, not inline in controllers.

## Python
- No mutable default arguments (`def f(x=[])`).
- Do not swallow exceptions with a bare `except:` or an empty `except Exception: pass`.
- Do not call `eval`/`exec` on external input; no secrets hardcoded in source.
- Use type hints on public functions.
