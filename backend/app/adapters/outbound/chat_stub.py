from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("/app/logs/outbound")


class ChatStubAdapter:
    name = "chat_stub"

    async def send(self, *, channel_thread_id: str, body_text: str) -> dict:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        record = {
            "channel": "chat",
            "channel_thread_id": channel_thread_id,
            "body_text": body_text,
            "sent_at": datetime.utcnow().isoformat() + "Z",
        }
        try:
            log_path = LOG_DIR / f"{datetime.utcnow():%Y%m%d}.jsonl"
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return {"ok": True, "channel": "chat", "channel_thread_id": channel_thread_id}
