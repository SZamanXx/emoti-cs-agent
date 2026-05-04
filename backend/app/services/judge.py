from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.llm.anthropic_client import LLMCallResult, call_anthropic
from app.llm.prompts.judge import JUDGE_PROMPT_VERSION, JUDGE_TOOL, build_judge_messages, judge_system_blocks

_settings = get_settings()


@dataclass
class JudgeResult:
    is_injection: bool
    confidence: float
    signals: list[str]
    raw: LLMCallResult


async def judge_injection(ticket_body: str) -> JudgeResult:
    res = await call_anthropic(
        model=_settings.anthropic_model_classifier,  # cheaper model for judge
        system=judge_system_blocks(),
        messages=build_judge_messages(ticket_body),
        tools=[JUDGE_TOOL],
        tool_choice={"type": "tool", "name": "verdict"},
        max_tokens=200,
        temperature=0.0,
    )
    inp = (res.tool_use or {}).get("input", {}) or {}
    return JudgeResult(
        is_injection=bool(inp.get("is_injection_attempt", False)),
        confidence=float(inp.get("confidence", 0.0)),
        signals=list(inp.get("signals", []) or []),
        raw=res,
    )


def get_prompt_version() -> str:
    return JUDGE_PROMPT_VERSION
