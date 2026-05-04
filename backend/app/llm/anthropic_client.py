from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import Message
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.llm.pricing import cost_for_call

_settings = get_settings()
_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=_settings.anthropic_api_key)
    return _client


@dataclass
class LLMUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_creation_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""

    @classmethod
    def from_message(cls, message: Message, model: str, cache_ttl: str = "5m") -> LLMUsage:
        usage = message.usage
        in_tok = getattr(usage, "input_tokens", 0) or 0
        out_tok = getattr(usage, "output_tokens", 0) or 0
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
        return cls(
            input_tokens=in_tok,
            cached_input_tokens=cached,
            cache_creation_tokens=creation,
            output_tokens=out_tok,
            cost_usd=cost_for_call(
                model,
                input_tokens=in_tok,
                cached_input_tokens=cached,
                cache_creation_tokens=creation,
                output_tokens=out_tok,
                cache_ttl=cache_ttl,
            ),
            model=model,
        )


@dataclass
class LLMCallResult:
    text: str
    tool_use: dict[str, Any] | None
    usage: LLMUsage
    raw: Message | None = None
    stop_reason: str | None = None


async def call_anthropic(
    *,
    model: str,
    system: list[dict[str, Any]] | str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: dict[str, Any] | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    cache_ttl: str = "5m",
    extra_headers: dict[str, str] | None = None,
) -> LLMCallResult:
    """Single-call wrapper with prompt caching support, retry, structured output extraction.

    `system` may be a string OR a list of content blocks. To enable prompt caching, pass
    a list whose blocks include {"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}.
    """
    client = get_client()

    kwargs: dict[str, Any] = dict(
        model=model,
        system=system if not isinstance(system, str) else [{"type": "text", "text": system}],
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if tools:
        kwargs["tools"] = tools
    if tool_choice:
        kwargs["tool_choice"] = tool_choice
    if extra_headers:
        kwargs["extra_headers"] = extra_headers

    last_exc: Exception | None = None
    msg: Message | None = None
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=False,
    ):
        with attempt:
            try:
                msg = await client.messages.create(**kwargs)
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                raise
    if msg is None:
        raise RuntimeError(f"Anthropic call failed after retries: {last_exc!r}")

    text_chunks: list[str] = []
    tool_use: dict[str, Any] | None = None
    for block in msg.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_chunks.append(getattr(block, "text", ""))
        elif block_type == "tool_use":
            tool_use = {
                "id": getattr(block, "id", None),
                "name": getattr(block, "name", None),
                "input": getattr(block, "input", {}) or {},
            }

    return LLMCallResult(
        text="\n".join(text_chunks).strip(),
        tool_use=tool_use,
        usage=LLMUsage.from_message(msg, model, cache_ttl=cache_ttl),
        raw=msg,
        stop_reason=getattr(msg, "stop_reason", None),
    )
