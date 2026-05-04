from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("/app/logs/outbound")


class EmailStubAdapter:
    """Stub: log-only. Production replacement would be Gmail OAuth, SMTP, or transactional ESP."""

    name = "email_stub"

    async def send(self, *, recipient: str, subject: str, body_text: str, body_html: str | None) -> dict:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        record = {
            "channel": "email",
            "recipient": recipient,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "sent_at": datetime.utcnow().isoformat() + "Z",
        }
        try:
            log_path = LOG_DIR / f"{datetime.utcnow():%Y%m%d}.jsonl"
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return {"ok": True, "channel": "email", "recipient": recipient}
