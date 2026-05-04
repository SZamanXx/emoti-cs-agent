from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.llm.anthropic_client import LLMCallResult, call_anthropic
from app.llm.prompts.classifier import (
    CLASSIFIER_PROMPT_VERSION,
    CLASSIFY_TOOL,
    build_classifier_messages,
    classifier_system_blocks,
)

_settings = get_settings()


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    suspected_injection: bool
    injection_signals: list[str]
    reasoning: str
    raw: LLMCallResult


async def classify(*, ticket_subject: str | None, ticket_body: str) -> ClassificationResult:
    res = await call_anthropic(
        model=_settings.anthropic_model_classifier,
        system=classifier_system_blocks(),
        messages=build_classifier_messages(ticket_subject, ticket_body),
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_ticket"},
        max_tokens=400,
        temperature=0.0,
    )
    if not res.tool_use or res.tool_use.get("name") != "classify_ticket":
        # graceful fallback
        return ClassificationResult(
            category="other",
            confidence=0.0,
            suspected_injection=False,
            injection_signals=[],
            reasoning="classifier did not return structured output",
            raw=res,
        )
    inp = res.tool_use.get("input", {}) or {}
    return ClassificationResult(
        category=str(inp.get("category", "other")),
        confidence=float(inp.get("confidence", 0.0)),
        suspected_injection=bool(inp.get("suspected_injection", False)),
        injection_signals=list(inp.get("injection_signals", []) or []),
        reasoning=str(inp.get("reasoning", "")),
        raw=res,
    )


def get_prompt_version() -> str:
    return CLASSIFIER_PROMPT_VERSION
