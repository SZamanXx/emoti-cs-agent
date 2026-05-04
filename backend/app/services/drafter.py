from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.llm.anthropic_client import LLMCallResult, call_anthropic
from app.llm.prompts.drafter import (
    DRAFTER_PROMPT_VERSION,
    DRAFTER_TOOL,
    build_drafter_messages,
    drafter_system_blocks,
)
from app.services.retriever import RetrievedChunk, format_kb_context

_settings = get_settings()


@dataclass
class DraftPayload:
    recipient: str | None
    subject: str | None
    body_text: str
    body_html: str | None
    requires_action: bool
    action_type: str | None
    action_params: dict[str, Any] | None
    confidence: float
    citations: list[dict[str, Any]]
    warnings: list[str]
    raw: LLMCallResult


async def generate_draft(
    *,
    ticket_subject: str | None,
    ticket_body: str,
    category: str,
    retrieved: list[RetrievedChunk],
    cms_context: str | None = None,
) -> DraftPayload:
    kb_context = format_kb_context(retrieved)
    res = await call_anthropic(
        model=_settings.anthropic_model_drafter,
        system=drafter_system_blocks(kb_context),
        messages=build_drafter_messages(
            ticket_subject=ticket_subject,
            ticket_body=ticket_body,
            category=category,
            cms_context=cms_context,
        ),
        tools=[DRAFTER_TOOL],
        tool_choice={"type": "tool", "name": "draft_reply"},
        max_tokens=1024,
        temperature=0.3,
    )

    inp = (res.tool_use or {}).get("input", {}) or {}

    citations_in = inp.get("citations") or []
    valid_chunk_ids = {c.chunk_id for c in retrieved}
    citations: list[dict[str, Any]] = []
    citation_warnings: list[str] = []
    for c in citations_in:
        cid = c.get("chunk_id")
        if cid in valid_chunk_ids:
            citations.append(
                {
                    "chunk_id": cid,
                    "snippet": c.get("snippet", "")[:300],
                    "document_title": next(
                        (rc.document_title for rc in retrieved if rc.chunk_id == cid), None
                    ),
                }
            )
        else:
            citation_warnings.append(f"hallucinated_citation:{cid}")

    warnings = list(inp.get("warnings", []) or []) + citation_warnings

    return DraftPayload(
        recipient=inp.get("recipient"),
        subject=inp.get("subject"),
        body_text=str(inp.get("body_text", "")).strip(),
        body_html=inp.get("body_html"),
        requires_action=bool(inp.get("requires_action", False)),
        action_type=inp.get("action_type"),
        action_params=inp.get("action_params"),
        confidence=float(inp.get("confidence", 0.0)),
        citations=citations,
        warnings=warnings,
        raw=res,
    )


def get_prompt_version() -> str:
    return DRAFTER_PROMPT_VERSION
