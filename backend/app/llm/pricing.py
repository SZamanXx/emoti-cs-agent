from __future__ import annotations

# Pricing per 1M tokens, USD. Numbers reflect public list pricing as of May 2026.
PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {
        "input": 1.00,
        "cache_write_5m": 1.25,
        "cache_write_1h": 2.00,
        "cache_read": 0.10,
        "output": 5.00,
    },
    "claude-sonnet-4-6": {
        "input": 3.00,
        "cache_write_5m": 3.75,
        "cache_write_1h": 6.00,
        "cache_read": 0.30,
        "output": 15.00,
    },
    # text-embedding-3-small via OpenAI
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}


def cost_for_call(
    model: str,
    *,
    input_tokens: int = 0,
    cached_input_tokens: int = 0,
    cache_creation_tokens: int = 0,
    output_tokens: int = 0,
    cache_ttl: str = "5m",
) -> float:
    p = PRICING.get(model)
    if not p:
        return 0.0
    cost = 0.0
    cost += (input_tokens / 1_000_000.0) * p.get("input", 0.0)
    cost += (cached_input_tokens / 1_000_000.0) * p.get("cache_read", 0.0)
    cw = p.get("cache_write_5m" if cache_ttl == "5m" else "cache_write_1h", p.get("input", 0.0))
    cost += (cache_creation_tokens / 1_000_000.0) * cw
    cost += (output_tokens / 1_000_000.0) * p.get("output", 0.0)
    return cost
