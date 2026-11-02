"""Token cost estimation. Prices (US$ per 1M tokens) live in ``prices.json``.

Only prices verified against the provider's official pricing page may be added.
"""

from __future__ import annotations

import json
from pathlib import Path

from reviewer.llm.base import Usage


def load_prices(path: Path | None = None) -> dict[str, dict[str, float]]:
    path = path or Path(__file__).with_name("prices.json")
    return json.loads(path.read_text(encoding="utf-8"))


def estimate_cost(
    model: str, usage: Usage, prices: dict[str, dict[str, float]] | None = None
) -> float | None:
    prices = load_prices() if prices is None else prices
    price = prices.get(model)
    if price is None:
        return None
    return (
        usage.prompt_tokens * price["input"] + usage.completion_tokens * price["output"]
    ) / 1_000_000
