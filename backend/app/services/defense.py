"""Layer-2 defense: pattern pre-filter for prompt-injection markers.

Layers 1 (XML delimiters) and 4 (output schema) are enforced in the prompts and tool schemas.
Layer 3 is `judge.py`. Layer 5 is privilege separation in adapters/cms (write operations are gated
behind explicit human approval).
"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass

# Patterns are intentionally English + Polish. Order: most specific first.
INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ignore_previous", re.compile(r"\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)\b", re.I)),
    ("ignore_polish", re.compile(r"\b(zignoruj|ignoruj)\s+(poprzednie|wszystkie)\s+(instrukcje|polecenia|reguły)\b", re.I)),
    ("you_are_now", re.compile(r"\byou\s+are\s+now\s+", re.I)),
    ("act_as", re.compile(r"\b(act\s+as|pretend\s+to\s+be|udawaj|zachowuj\s+się\s+jak)\b", re.I)),
    ("system_role_marker", re.compile(r"<\|?\s*system\s*\|?>|^\s*system\s*:\s*", re.I | re.M)),
    ("override_directive", re.compile(r"\b(override|bypass|disregard|disable)\s+(?:the\s+|all\s+|any\s+)?(safety|restrictions?|filter|guardrails?)\b", re.I)),
    ("reveal_prompt", re.compile(r"\b(reveal|show|print|tell\s+me|repeat)\s+(your\s+)?(system\s+)?(prompt|instructions)\b", re.I)),
    ("ai_meta", re.compile(r"\bif\s+you\s+are\s+(an?\s+)?(ai|llm|language\s+model)\b", re.I)),
    ("execute_function", re.compile(r"\b(call|invoke|execute)\s+(the\s+)?(function|tool)\b", re.I)),
    ("policy_override", re.compile(r"\b(emergency|urgent)\s+(override|directive|protocol)\b", re.I)),
]

URL_RE = re.compile(r"https?://([\w\-\.]+)(/[^\s]*)?", re.I)
SUSPICIOUS_TLDS = {"xyz", "top", "click", "link", "tk", "ml", "ga", "cf"}
INVISIBLE_TAG_RE = re.compile(
    r"[\u00ad\u200b\u200c\u200d\u2060\ufeff]|[\U000E0000-\U000E007F]"
)
BASE64_LIKELY_RE = re.compile(r"(?:[A-Za-z0-9+/]{40,}={0,2})")


@dataclass
class PreFilterResult:
    suspected: bool
    signals: list[str]


def run_pre_filter(text: str) -> PreFilterResult:
    if not text:
        return PreFilterResult(False, [])
    signals: list[str] = []
    for label, pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            signals.append(label)

    for match in URL_RE.finditer(text):
        host = match.group(1) or ""
        tld = host.rsplit(".", 1)[-1].lower() if "." in host else ""
        if tld in SUSPICIOUS_TLDS:
            signals.append(f"suspicious_tld:{tld}")

    if INVISIBLE_TAG_RE.search(text):
        signals.append("invisible_unicode")

    for blob in BASE64_LIKELY_RE.findall(text):
        try:
            decoded = base64.b64decode(blob, validate=True).decode("utf-8", errors="ignore")
        except Exception:
            continue
        if decoded and any(p[1].search(decoded) for p in INJECTION_PATTERNS):
            signals.append("base64_injection_payload")
            break

    return PreFilterResult(suspected=bool(signals), signals=signals)


def sanitize_for_logging(text: str, max_chars: int = 400) -> str:
    """Lightweight PII masking + truncation for safe log output."""
    if not text:
        return ""
    masked = re.sub(r"[\w\.+-]+@[\w\.-]+\.\w+", "[email]", text)
    masked = re.sub(r"\b\d{9,}\b", "[id]", masked)
    if len(masked) > max_chars:
        masked = masked[:max_chars] + "…"
    return masked
